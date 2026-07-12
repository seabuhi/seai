#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <memory>
#include <numeric>
#include <random>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <map>
#include <string>
#include <fstream>
#include <sstream>
#include <chrono>

class Tensor : public std::enable_shared_from_this<Tensor> {
public:
  std::vector<float> data;
  std::vector<float> grad;
  std::vector<int> shape;
  int size;
  std::vector<std::shared_ptr<Tensor>> prev;
  std::function<void()> _backward;

  Tensor(std::vector<int> s, std::vector<std::shared_ptr<Tensor>> p = {})
      : shape(s), prev(p) {
    size = 1;
    for (int dim : shape)
      size *= dim;
    data.resize(size, 0.0f);
    grad.resize(size, 0.0f);
    _backward = []() {};
  }

  static std::shared_ptr<Tensor> make(std::vector<int> s, std::vector<std::shared_ptr<Tensor>> p = {}) {
      return std::make_shared<Tensor>(s, p);
  }

  void randomize(float mean=0.0f, float stddev=0.1f) {
    static std::mt19937 gen(42);
    std::normal_distribution<float> distribution(mean, stddev);
    for (int i = 0; i < size; ++i) {
      data[i] = distribution(gen);
    }
  }

  static std::shared_ptr<Tensor> matmul(std::shared_ptr<Tensor> a,
                                        std::shared_ptr<Tensor> b) {
    if (a->shape.size() != 2 || b->shape.size() != 2 ||
        a->shape[1] != b->shape[0]) {
      throw std::runtime_error("Invalid shapes for matmul");
    }

    int M = a->shape[0];
    int K = a->shape[1];
    int N = b->shape[1];
    auto res = Tensor::make(std::vector<int>{M, N}, {a, b});

    #pragma omp parallel for schedule(static)
    for (int i = 0; i < M; ++i) {
      for (int k = 0; k < K; ++k) {
        float val = a->data[i * K + k];
        for (int j = 0; j < N; ++j) {
          res->data[i * N + j] += val * b->data[k * N + j];
        }
      }
    }

    Tensor* res_ptr = res.get();
    res->_backward = [a, b, res_ptr, M, K, N]() {
      #pragma omp parallel for schedule(static)
      for (int i = 0; i < M; ++i) {
        for (int k = 0; k < K; ++k) {
          float sum = 0;
          for (int j = 0; j < N; ++j) {
            sum += res_ptr->grad[i * N + j] * b->data[k * N + j];
          }
          a->grad[i * K + k] += sum;
        }
      }
      #pragma omp parallel for schedule(static)
      for (int k = 0; k < K; ++k) {
        for (int i = 0; i < M; ++i) {
          float val = a->data[i * K + k];
          for (int j = 0; j < N; ++j) {
            b->grad[k * N + j] += val * res_ptr->grad[i * N + j];
          }
        }
      }
    };

    return res;
  }

  static std::shared_ptr<Tensor> add(std::shared_ptr<Tensor> a, std::shared_ptr<Tensor> b) {
      if (a->shape.size() != 2 || b->shape.size() != 2) {
          throw std::runtime_error("Only 2D tensors supported for add");
      }
      if (a->shape[1] != b->shape[1]) {
          throw std::runtime_error("Dimension mismatch in add (dim 1)");
      }
      bool broadcast = (a->shape[0] != b->shape[0]);
      if (broadcast && b->shape[0] != 1) {
          throw std::runtime_error("Broadcasting only supported for 1xN added to MxN");
      }
      
      int M = a->shape[0];
      int N = a->shape[1];
      auto res = Tensor::make({M, N}, {a, b});

      for (int i = 0; i < M; ++i) {
          for (int j = 0; j < N; ++j) {
              int b_i = broadcast ? 0 : i;
              res->data[i * N + j] = a->data[i * N + j] + b->data[b_i * N + j];
          }
      }

      Tensor* res_ptr = res.get();
      res->_backward = [a, b, res_ptr, M, N, broadcast]() {
          for (int i = 0; i < M; ++i) {
              for (int j = 0; j < N; ++j) {
                  a->grad[i * N + j] += res_ptr->grad[i * N + j];
                  int b_i = broadcast ? 0 : i;
                  b->grad[b_i * N + j] += res_ptr->grad[i * N + j];
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> relu(std::shared_ptr<Tensor> a) {
      auto res = Tensor::make(a->shape, {a});
      for (int i = 0; i < a->size; ++i) {
          res->data[i] = std::max(0.0f, a->data[i]);
      }
      Tensor* res_ptr = res.get();
      res->_backward = [a, res_ptr]() {
          for (int i = 0; i < a->size; ++i) {
              if (res_ptr->data[i] > 0) {
                  a->grad[i] += res_ptr->grad[i];
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> gather(std::shared_ptr<Tensor> w, const std::vector<int>& indices) {
      if (w->shape.size() != 2) throw std::runtime_error("Gather expects 2D weight matrix");
      int vocab_size = w->shape[0];
      int embed_dim = w->shape[1];
      int seq_len = indices.size();

      auto res = Tensor::make({seq_len, embed_dim}, {w});

      for (int i = 0; i < seq_len; ++i) {
          int idx = indices[i];
          if (idx < 0 || idx >= vocab_size) throw std::runtime_error("Index out of bounds in gather");
          for (int j = 0; j < embed_dim; ++j) {
              res->data[i * embed_dim + j] = w->data[idx * embed_dim + j];
          }
      }

      Tensor* res_ptr = res.get();
      res->_backward = [w, res_ptr, indices, seq_len, embed_dim]() {
          for (int i = 0; i < seq_len; ++i) {
              int idx = indices[i];
              for (int j = 0; j < embed_dim; ++j) {
                  w->grad[idx * embed_dim + j] += res_ptr->grad[i * embed_dim + j];
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> transpose(std::shared_ptr<Tensor> a) {
      if (a->shape.size() != 2) throw std::runtime_error("Transpose only for 2D");
      int M = a->shape[0];
      int N = a->shape[1];
      auto res = Tensor::make({N, M}, {a});
      for (int i = 0; i < M; ++i) {
          for (int j = 0; j < N; ++j) {
              res->data[j * M + i] = a->data[i * N + j];
          }
      }
      Tensor* res_ptr = res.get();
      res->_backward = [a, res_ptr, M, N]() {
          for (int i = 0; i < M; ++i) {
              for (int j = 0; j < N; ++j) {
                  a->grad[i * N + j] += res_ptr->grad[j * M + i];
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> scale(std::shared_ptr<Tensor> a, float factor) {
      auto res = Tensor::make(a->shape, {a});
      for(int i=0; i<a->size; ++i) res->data[i] = a->data[i] * factor;
      Tensor* res_ptr = res.get();
      res->_backward = [a, res_ptr, factor]() {
          for(int i=0; i<a->size; ++i) a->grad[i] += res_ptr->grad[i] * factor;
      };
      return res;
  }

  static std::shared_ptr<Tensor> causal_mask(std::shared_ptr<Tensor> a) {
      if (a->shape.size() != 2) throw std::runtime_error("Causal mask requires 2D");
      int M = a->shape[0];
      int N = a->shape[1];
      auto res = Tensor::make({M, N}, {a});
      for (int i = 0; i < M; ++i) {
          for (int j = 0; j < N; ++j) {
              if (j > i) res->data[i * N + j] = -1e9f;
              else res->data[i * N + j] = a->data[i * N + j];
          }
      }
      Tensor* res_ptr = res.get();
      res->_backward = [a, res_ptr, M, N]() {
          for (int i = 0; i < M; ++i) {
              for (int j = 0; j < N; ++j) {
                  if (j <= i) a->grad[i * N + j] += res_ptr->grad[i * N + j];
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> softmax(std::shared_ptr<Tensor> a) {
      if (a->shape.size() != 2) throw std::runtime_error("Softmax requires 2D");
      int M = a->shape[0];
      int N = a->shape[1];
      auto res = Tensor::make({M, N}, {a});

      for (int i = 0; i < M; ++i) {
          float max_val = -1e9f;
          for (int j = 0; j < N; ++j) {
              if (a->data[i * N + j] > max_val) max_val = a->data[i * N + j];
          }
          float sum_exp = 0.0f;
          for (int j = 0; j < N; ++j) {
              float e = std::exp(a->data[i * N + j] - max_val);
              res->data[i * N + j] = e;
              sum_exp += e;
          }
          for (int j = 0; j < N; ++j) {
              res->data[i * N + j] /= sum_exp;
          }
      }

      Tensor* res_ptr = res.get();
      res->_backward = [a, res_ptr, M, N]() {
          #pragma omp parallel for schedule(static)
          for (int i = 0; i < M; ++i) {
              float sum_y_grad = 0.0f;
              for (int j = 0; j < N; ++j) {
                  sum_y_grad += res_ptr->data[i * N + j] * res_ptr->grad[i * N + j];
              }
              for (int k = 0; k < N; ++k) {
                  float y_k = res_ptr->data[i * N + k];
                  a->grad[i * N + k] += y_k * (res_ptr->grad[i * N + k] - sum_y_grad);
              }
          }
      };
      return res;
  }

  static std::shared_ptr<Tensor> concat(const std::vector<std::shared_ptr<Tensor>>& tensors) {
      if (tensors.empty()) throw std::runtime_error("Concat empty vector");
      int M = tensors[0]->shape[0];
      int out_N = 0;
      for (auto t : tensors) {
          if (t->shape[0] != M) throw std::runtime_error("Concat shape mismatch (dim 0)");
          out_N += t->shape[1];
      }
      
      auto res = Tensor::make({M, out_N}, tensors);
      
      int current_col = 0;
      for (auto t : tensors) {
          int N = t->shape[1];
          for (int i = 0; i < M; ++i) {
              for (int j = 0; j < N; ++j) {
                  res->data[i * out_N + current_col + j] = t->data[i * N + j];
              }
          }
          current_col += N;
      }
      
      Tensor* res_ptr = res.get();
      res->_backward = [tensors, res_ptr, M, out_N]() {
          int current_col = 0;
          for (auto t : tensors) {
              int N = t->shape[1];
              for (int i = 0; i < M; ++i) {
                  for (int j = 0; j < N; ++j) {
                      t->grad[i * N + j] += res_ptr->grad[i * out_N + current_col + j];
                  }
              }
              current_col += N;
          }
      };
      return res;
  }

  // --- Phase 6: Cross-Entropy Loss (Fused Softmax + NLL) ---
  // logits: [N, V] raw scores (before softmax)
  // targets: integer class indices, length N
  // Loss = -mean( log( softmax(logits)[i, targets[i]] ) )
  static std::shared_ptr<Tensor> cross_entropy(
      std::shared_ptr<Tensor> logits,
      const std::vector<int>& targets) {

    if (logits->shape.size() != 2) throw std::runtime_error("cross_entropy: logits must be 2D [N, V]");
    int N = logits->shape[0];
    int V = logits->shape[1];
    if ((int)targets.size() != N) throw std::runtime_error("cross_entropy: targets length mismatch");

    auto res = Tensor::make({1, 1}, {logits});

    // Compute stable softmax probabilities
    std::vector<float> probs(N * V);
    for (int i = 0; i < N; ++i) {
        float max_val = *std::max_element(
            logits->data.begin() + i * V,
            logits->data.begin() + i * V + V);
        float sum_exp = 0.0f;
        for (int j = 0; j < V; ++j) {
            probs[i * V + j] = std::exp(logits->data[i * V + j] - max_val);
            sum_exp += probs[i * V + j];
        }
        for (int j = 0; j < V; ++j) probs[i * V + j] /= sum_exp;
    }

    // NLL loss: -mean(log p[target])
    float loss = 0.0f;
    for (int i = 0; i < N; ++i) {
        int t = targets[i];
        if (t < 0 || t >= V) throw std::runtime_error("cross_entropy: target index out of range");
        loss -= std::log(probs[i * V + t] + 1e-9f);
    }
    res->data[0] = loss / N;

    // Backward: dL/dlogits_ij = (p_ij - 1[j==target_i]) / N
    Tensor* res_ptr = res.get();
    res->_backward = [logits, res_ptr, N, V, probs, targets]() {
        float scale = res_ptr->grad[0] / N;
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < V; ++j) {
                float indicator = (j == targets[i]) ? 1.0f : 0.0f;
                logits->grad[i * V + j] += scale * (probs[i * V + j] - indicator);
            }
        }
    };
    return res;
  }

  // --- Phase 5: Fused Layer Normalization ---
  // LayerNorm normalizes across the last dimension (feature dim).
  // Forward:  y = gamma * (x - mean) / sqrt(var + eps) + beta
  // Backward: Jacobian-based gradient for dx, dgamma, dbeta
  static std::shared_ptr<Tensor> layer_norm(
      std::shared_ptr<Tensor> x,
      std::shared_ptr<Tensor> gamma, // shape {1, D}
      std::shared_ptr<Tensor> beta,  // shape {1, D}
      float eps = 1e-5f) {

    if (x->shape.size() != 2) throw std::runtime_error("layer_norm requires 2D input [N, D]");
    int N = x->shape[0]; // sequence length (or batch)
    int D = x->shape[1]; // feature dimension
    if (gamma->shape[0] != 1 || gamma->shape[1] != D)
        throw std::runtime_error("gamma shape mismatch in layer_norm");
    if (beta->shape[0] != 1 || beta->shape[1] != D)
        throw std::runtime_error("beta shape mismatch in layer_norm");

    auto res = Tensor::make({N, D}, {x, gamma, beta});

    // Save mean and inv_std for each row (needed in backward)
    std::vector<float> means(N), inv_stds(N), x_hat(N * D);

    for (int i = 0; i < N; ++i) {
        // Compute mean
        float mean = 0.0f;
        for (int j = 0; j < D; ++j) mean += x->data[i * D + j];
        mean /= D;
        means[i] = mean;

        // Compute variance
        float var = 0.0f;
        for (int j = 0; j < D; ++j) {
            float diff = x->data[i * D + j] - mean;
            var += diff * diff;
        }
        var /= D;
        float inv_std = 1.0f / std::sqrt(var + eps);
        inv_stds[i] = inv_std;

        // Compute x_hat and output
        for (int j = 0; j < D; ++j) {
            float xh = (x->data[i * D + j] - mean) * inv_std;
            x_hat[i * D + j] = xh;
            res->data[i * D + j] = gamma->data[j] * xh + beta->data[j];
        }
    }

    // Backward pass: Jacobian of LayerNorm
    // Reference: https://arxiv.org/abs/1607.06450 Appendix
    // dx_hat = dout * gamma
    // dvar   = sum(dx_hat * (x - mean) * -0.5 * inv_std^3)
    // dmean  = sum(dx_hat * -inv_std) + dvar * sum(-2*(x-mean))/D
    // dx     = dx_hat * inv_std + dvar * 2*(x-mean)/D + dmean/D
    Tensor* res_ptr = res.get();
    res->_backward = [x, gamma, beta, res_ptr, N, D, means, inv_stds, x_hat, eps]() {
        for (int i = 0; i < N; ++i) {
            float inv_std = inv_stds[i];
            float mean    = means[i];

            // Step 1: dx_hat = dout * gamma
            std::vector<float> dx_hat(D);
            for (int j = 0; j < D; ++j) {
                dx_hat[j] = res_ptr->grad[i * D + j] * gamma->data[j];
                // Accumulate dgamma and dbeta
                gamma->grad[j] += res_ptr->grad[i * D + j] * x_hat[i * D + j];
                beta->grad[j]  += res_ptr->grad[i * D + j];
            }

            // Step 2: dvar
            float dvar = 0.0f;
            for (int j = 0; j < D; ++j) {
                float x_minus_mean = x->data[i * D + j] - mean;
                dvar += dx_hat[j] * x_minus_mean * (-0.5f) * inv_std * inv_std * inv_std;
            }

            // Step 3: dmean
            float dmean = 0.0f;
            for (int j = 0; j < D; ++j) {
                dmean += dx_hat[j] * (-inv_std);
            }
            // dvar contribution to dmean
            float sum_x_minus_mean = 0.0f;
            for (int j = 0; j < D; ++j) sum_x_minus_mean += x->data[i * D + j] - mean;
            dmean += dvar * (-2.0f / D) * sum_x_minus_mean;

            // Step 4: dx
            for (int j = 0; j < D; ++j) {
                float x_minus_mean = x->data[i * D + j] - mean;
                x->grad[i * D + j] += dx_hat[j] * inv_std
                                    + dvar * 2.0f * x_minus_mean / D
                                    + dmean / D;
            }
        }
    };
    return res;
  }

  static std::shared_ptr<Tensor> mse_loss(std::shared_ptr<Tensor> pred, std::shared_ptr<Tensor> target) {
      if (pred->size != target->size) throw std::runtime_error("Size mismatch in mse_loss");
      auto res = Tensor::make({1, 1}, {pred, target});
      float sum = 0.0f;
      for (int i = 0; i < pred->size; ++i) {
          float diff = pred->data[i] - target->data[i];
          sum += diff * diff;
      }
      res->data[0] = sum / pred->size;
      
      Tensor* res_ptr = res.get();
      res->_backward = [pred, target, res_ptr]() {
          float factor = 2.0f / pred->size;
          for (int i = 0; i < pred->size; ++i) {
              float grad_val = factor * (pred->data[i] - target->data[i]) * res_ptr->grad[0];
              pred->grad[i] += grad_val;
              target->grad[i] -= grad_val;
          }
      };
      return res;
  }

  void backward() {
    std::vector<std::shared_ptr<Tensor>> topo;
    std::unordered_set<Tensor*> visited;

    std::function<void(std::shared_ptr<Tensor>)> build_topo =
        [&](std::shared_ptr<Tensor> v) {
          if (visited.find(v.get()) == visited.end()) {
            visited.insert(v.get());
            for (auto p : v->prev) build_topo(p);
            topo.push_back(v);
          }
        };

    build_topo(shared_from_this());
    grad[0] = 1.0f;

    std::reverse(topo.begin(), topo.end());
    for (auto v : topo) v->_backward();
  }

  void print() {
    for (int i = 0; i < shape[0]; ++i) {
      for (int j = 0; j < shape[1]; ++j) {
        std::cout << data[i * shape[1] + j] << " ";
      }
      std::cout << "\n";
    }
  }
};

class Module {
public:
    virtual std::vector<std::shared_ptr<Tensor>> parameters() = 0;
};

class Linear : public Module {
public:
    std::shared_ptr<Tensor> W;
    std::shared_ptr<Tensor> b;

    Linear(int in_features, int out_features) {
        W = Tensor::make({in_features, out_features});
        float stddev = std::sqrt(2.0f / in_features);
        W->randomize(0.0f, stddev);
        b = Tensor::make({1, out_features}); 
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x) {
        return Tensor::add(Tensor::matmul(x, W), b);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        return {W, b};
    }
};

class Embedding : public Module {
public:
    std::shared_ptr<Tensor> weight;

    Embedding(int num_embeddings, int embedding_dim) {
        weight = Tensor::make({num_embeddings, embedding_dim});
        weight->randomize(0.0f, 0.02f);
    }

    std::shared_ptr<Tensor> forward(const std::vector<int>& indices) {
        return Tensor::gather(weight, indices);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        return {weight};
    }
};

class SelfAttention : public Module {
public:
    std::shared_ptr<Linear> q_proj;
    std::shared_ptr<Linear> k_proj;
    std::shared_ptr<Linear> v_proj;
    int head_dim;

    SelfAttention(int embed_dim, int head_dim) : head_dim(head_dim) {
        q_proj = std::make_shared<Linear>(embed_dim, head_dim);
        k_proj = std::make_shared<Linear>(embed_dim, head_dim);
        v_proj = std::make_shared<Linear>(embed_dim, head_dim);
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x, bool causal = true) {
        auto q = q_proj->forward(x);
        auto k = k_proj->forward(x);
        auto v = v_proj->forward(x);

        auto k_t = Tensor::transpose(k);
        auto scores = Tensor::matmul(q, k_t); // [seq_len, seq_len]
        
        float scale_factor = 1.0f / std::sqrt((float)head_dim);
        scores = Tensor::scale(scores, scale_factor);

        if (causal) {
            scores = Tensor::causal_mask(scores);
        }

        auto weights = Tensor::softmax(scores);
        return Tensor::matmul(weights, v);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        auto params = q_proj->parameters();
        auto kp = k_proj->parameters();
        auto vp = v_proj->parameters();
        params.insert(params.end(), kp.begin(), kp.end());
        params.insert(params.end(), vp.begin(), vp.end());
        return params;
    }
};

class MultiHeadAttention : public Module {
public:
    std::vector<std::shared_ptr<SelfAttention>> heads;
    std::shared_ptr<Linear> o_proj;

    MultiHeadAttention(int embed_dim, int num_heads) {
        if (embed_dim % num_heads != 0) throw std::runtime_error("embed_dim must be div by num_heads");
        int head_dim = embed_dim / num_heads;
        
        for (int i = 0; i < num_heads; ++i) {
            heads.push_back(std::make_shared<SelfAttention>(embed_dim, head_dim));
        }
        o_proj = std::make_shared<Linear>(embed_dim, embed_dim);
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x, bool causal = true) {
        std::vector<std::shared_ptr<Tensor>> head_outputs;
        for (auto head : heads) {
            head_outputs.push_back(head->forward(x, causal));
        }
        
        auto concat_out = Tensor::concat(head_outputs);
        return o_proj->forward(concat_out);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        std::vector<std::shared_ptr<Tensor>> params;
        for (auto head : heads) {
            auto hp = head->parameters();
            params.insert(params.end(), hp.begin(), hp.end());
        }
        auto op = o_proj->parameters();
        params.insert(params.end(), op.begin(), op.end());
        return params;
    }
};

// --- Phase 5: LayerNorm Module ---
class LayerNorm : public Module {
public:
    std::shared_ptr<Tensor> gamma; // scale, init=1
    std::shared_ptr<Tensor> beta;  // shift, init=0
    float eps;

    LayerNorm(int dim, float eps = 1e-5f) : eps(eps) {
        gamma = Tensor::make({1, dim});
        beta  = Tensor::make({1, dim});
        // gamma = 1, beta = 0 (identity transform by default)
        for (int i = 0; i < dim; ++i) {
            gamma->data[i] = 1.0f;
            beta->data[i]  = 0.0f;
        }
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x) {
        return Tensor::layer_norm(x, gamma, beta, eps);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        return {gamma, beta};
    }
};

// --- Phase 5: MLP (Feed-Forward Network) ---
// GPT-style: expand 4x -> ReLU -> project back
class MLP : public Module {
public:
    std::shared_ptr<Linear> fc1;
    std::shared_ptr<Linear> fc2;

    MLP(int embed_dim) {
        int ffn_dim = 4 * embed_dim; // standard GPT expansion factor
        fc1 = std::make_shared<Linear>(embed_dim, ffn_dim);
        fc2 = std::make_shared<Linear>(ffn_dim, embed_dim);
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x) {
        auto h = fc1->forward(x);
        h = Tensor::relu(h);
        return fc2->forward(h);
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        auto p1 = fc1->parameters();
        auto p2 = fc2->parameters();
        p1.insert(p1.end(), p2.begin(), p2.end());
        return p1;
    }
};

// --- Phase 5: TransformerBlock ---
// Pre-LN Residual Architecture (GPT-2 style):
//   h = x   + MHA(LayerNorm1(x))
//   out = h + MLP(LayerNorm2(h))
class TransformerBlock : public Module {
public:
    std::shared_ptr<LayerNorm>        ln1;
    std::shared_ptr<MultiHeadAttention> mha;
    std::shared_ptr<LayerNorm>        ln2;
    std::shared_ptr<MLP>              mlp;

    TransformerBlock(int embed_dim, int num_heads) {
        ln1 = std::make_shared<LayerNorm>(embed_dim);
        mha = std::make_shared<MultiHeadAttention>(embed_dim, num_heads);
        ln2 = std::make_shared<LayerNorm>(embed_dim);
        mlp = std::make_shared<MLP>(embed_dim);
    }

    std::shared_ptr<Tensor> forward(std::shared_ptr<Tensor> x, bool causal = true) {
        // Sub-layer 1: Self-Attention with residual
        auto norm1_out = ln1->forward(x);
        auto attn_out  = mha->forward(norm1_out, causal);
        auto h = Tensor::add(x, attn_out); // residual connection

        // Sub-layer 2: MLP with residual
        auto norm2_out = ln2->forward(h);
        auto mlp_out   = mlp->forward(norm2_out);
        auto out = Tensor::add(h, mlp_out); // residual connection

        return out;
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        std::vector<std::shared_ptr<Tensor>> params;
        auto p1 = ln1->parameters();
        auto p2 = mha->parameters();
        auto p3 = ln2->parameters();
        auto p4 = mlp->parameters();
        params.insert(params.end(), p1.begin(), p1.end());
        params.insert(params.end(), p2.begin(), p2.end());
        params.insert(params.end(), p3.begin(), p3.end());
        params.insert(params.end(), p4.begin(), p4.end());
        return params;
    }
};

// ============================================================
// Phase 6: Mini GPT
// ============================================================
class MiniGPT : public Module {
public:
    std::shared_ptr<Embedding>   tok_emb;  // token embeddings
    std::shared_ptr<Embedding>   pos_emb;  // learned positional embeddings
    std::vector<std::shared_ptr<TransformerBlock>> blocks;
    std::shared_ptr<LayerNorm>   ln_f;     // final layer norm
    std::shared_ptr<Linear>      lm_head;  // project to vocab
    int max_seq_len;

    MiniGPT(int vocab_size, int embed_dim, int num_heads,
            int num_layers, int max_seq_len)
        : max_seq_len(max_seq_len) {
        tok_emb = std::make_shared<Embedding>(vocab_size, embed_dim);
        pos_emb = std::make_shared<Embedding>(max_seq_len, embed_dim);
        for (int i = 0; i < num_layers; ++i)
            blocks.push_back(std::make_shared<TransformerBlock>(embed_dim, num_heads));
        ln_f    = std::make_shared<LayerNorm>(embed_dim);
        lm_head = std::make_shared<Linear>(embed_dim, vocab_size);
        // Zero-init lm_head weights for stable early training
        for (float& w : lm_head->W->data) w = 0.0f;
        for (float& b : lm_head->b->data) b = 0.0f;
    }

    // tokens: integer sequence of length T
    // Returns logits: [T, vocab_size]
    std::shared_ptr<Tensor> forward(const std::vector<int>& tokens) {
        int T = (int)tokens.size();
        if (T > max_seq_len) throw std::runtime_error("Sequence too long for MiniGPT");

        std::vector<int> positions(T);
        std::iota(positions.begin(), positions.end(), 0);

        auto tok = tok_emb->forward(tokens);    // [T, D]
        auto pos = pos_emb->forward(positions); // [T, D]
        auto x   = Tensor::add(tok, pos);       // [T, D]

        for (auto& block : blocks)
            x = block->forward(x, /*causal=*/true);

        x = ln_f->forward(x);       // final layer norm
        return lm_head->forward(x); // [T, vocab_size]
    }

    std::vector<std::shared_ptr<Tensor>> parameters() override {
        std::vector<std::shared_ptr<Tensor>> params;
        auto append = [&](std::vector<std::shared_ptr<Tensor>> p) {
            params.insert(params.end(), p.begin(), p.end());
        };
        append(tok_emb->parameters());
        append(pos_emb->parameters());
        for (auto& b : blocks) append(b->parameters());
        append(ln_f->parameters());
        append(lm_head->parameters());
        return params;
    }
};

class Optimizer {
public:
    std::vector<std::shared_ptr<Tensor>> parameters;
    Optimizer(std::vector<std::shared_ptr<Tensor>> params) : parameters(params) {}
    virtual void step() = 0;
    void zero_grad() {
        for (auto p : parameters) {
            for (float &g : p->grad) g = 0.0f;
        }
    }
};

class AdamW : public Optimizer {
public:
    float lr, beta1, beta2, eps, weight_decay;
    int t;
    std::vector<std::vector<float>> m;
    std::vector<std::vector<float>> v;

    AdamW(std::vector<std::shared_ptr<Tensor>> params, float lr=1e-3f, float beta1=0.9f, float beta2=0.999f, float eps=1e-8f, float weight_decay=0.01f) 
        : Optimizer(params), lr(lr), beta1(beta1), beta2(beta2), eps(eps), weight_decay(weight_decay), t(0) {
        m.resize(parameters.size());
        v.resize(parameters.size());
        for (size_t i = 0; i < parameters.size(); ++i) {
            m[i] = std::vector<float>(parameters[i]->size, 0.0f);
            v[i] = std::vector<float>(parameters[i]->size, 0.0f);
        }
    }

    void step() override {
        t++;
        float corr1 = 1.0f - std::pow(beta1, t);
        float corr2 = 1.0f - std::pow(beta2, t);
        
        #pragma omp parallel for schedule(dynamic)
        for (int p_idx = 0; p_idx < (int)parameters.size(); ++p_idx) {
            auto p = parameters[p_idx];
            std::vector<float>& m_t = m[p_idx];
            std::vector<float>& v_t = v[p_idx];

            for (int i = 0; i < p->size; ++i) {
                p->data[i] -= lr * weight_decay * p->data[i];
                float grad = p->grad[i];
                m_t[i] = beta1 * m_t[i] + (1.0f - beta1) * grad;
                v_t[i] = beta2 * v_t[i] + (1.0f - beta2) * grad * grad;

                float m_hat = m_t[i] / corr1;
                float v_hat = v_t[i] / corr2;

                p->data[i] -= lr * m_hat / (std::sqrt(v_hat) + eps);
            }
        }
    }
};

// ============================================================
// Phase 7: BPE Tokenizer (Byte-Pair Encoding)
// ============================================================
struct BPETokenizer {
    std::unordered_map<int, std::string> id2vocab;
    std::unordered_map<std::string, int> vocab2id;
    std::vector<std::pair<int, int>> merges;
    int vocab_size;

    void train(const std::string& text, int num_merges) {
        // Step 1: Start with character-level vocabulary
        std::vector<char> chars(text.begin(), text.end());
        std::sort(chars.begin(), chars.end());
        chars.erase(std::unique(chars.begin(), chars.end()), chars.end());
        
        vocab_size = 0;
        for (char c : chars) {
            std::string s(1, c);
            id2vocab[vocab_size] = s;
            vocab2id[s] = vocab_size;
            vocab_size++;
        }

        // Convert text to initial IDs
        std::vector<int> ids;
        for (char c : text) {
            ids.push_back(vocab2id[std::string(1, c)]);
        }

        // Step 2: BPE Iterations
        for (int i = 0; i < num_merges; ++i) {
            if (ids.size() < 2) break;

            // Count pair frequencies
            std::map<std::pair<int, int>, int> stats;
            for (size_t j = 0; j < ids.size() - 1; ++j) {
                stats[{ids[j], ids[j+1]}]++;
            }

            // Find most frequent pair
            int max_count = 0;
            std::pair<int, int> best_pair;
            for (auto const& [pair, count] : stats) {
                if (count > max_count) {
                    max_count = count;
                    best_pair = pair;
                }
            }

            if (max_count < 2) break; // Nothing to merge

            // Add new token to vocabulary
            std::string new_token = id2vocab[best_pair.first] + id2vocab[best_pair.second];
            int new_id = vocab_size++;
            id2vocab[new_id] = new_token;
            vocab2id[new_token] = new_id;
            merges.push_back(best_pair);

            // Replace pair with new token in the sequence
            std::vector<int> new_ids;
            for (size_t j = 0; j < ids.size(); ++j) {
                if (j < ids.size() - 1 && ids[j] == best_pair.first && ids[j+1] == best_pair.second) {
                    new_ids.push_back(new_id);
                    j++; // Skip next token
                } else {
                    new_ids.push_back(ids[j]);
                }
            }
            ids = new_ids;
        }
    }

    std::vector<int> encode(const std::string& text) const {
        // Start with character IDs
        std::vector<int> ids;
        for (char c : text) {
            std::string s(1, c);
            if (vocab2id.count(s)) ids.push_back(vocab2id.at(s));
            // else ignore unknown chars for this basic implementation
        }

        // Apply merges in the exact order they were learned
        for (auto const& merge_pair : merges) {
            std::vector<int> new_ids;
            for (size_t i = 0; i < ids.size(); ++i) {
                if (i < ids.size() - 1 && ids[i] == merge_pair.first && ids[i+1] == merge_pair.second) {
                    std::string new_token = id2vocab.at(ids[i]) + id2vocab.at(ids[i+1]);
                    new_ids.push_back(vocab2id.at(new_token));
                    i++; // Skip the merged token
                } else {
                    new_ids.push_back(ids[i]);
                }
            }
            ids = new_ids;
        }
        return ids;
    }

    std::string decode(const std::vector<int>& ids) const {
        std::string out;
        for (int id : ids) {
            if (id2vocab.count(id)) out += id2vocab.at(id);
        }
        return out;
    }
};

// ============================================================
// Phase 9: Model & Tokenizer Persistence
// ============================================================

void save_weights(const std::vector<std::shared_ptr<Tensor>>& params,
                  const std::string& path) {
    std::ofstream f(path, std::ios::binary);
    for (auto& p : params)
        f.write(reinterpret_cast<const char*>(p->data.data()),
                p->size * sizeof(float));
}

bool load_weights(const std::vector<std::shared_ptr<Tensor>>& params,
                  const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f.is_open()) return false;
    for (auto& p : params) {
        f.read(reinterpret_cast<char*>(p->data.data()),
               p->size * sizeof(float));
        if (f.fail()) return false;
    }
    return true;
}

void save_bpe(const BPETokenizer& tok, const std::string& path) {
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char*>(&tok.vocab_size), sizeof(int));
    for (int id = 0; id < tok.vocab_size; ++id) {
        auto it = tok.id2vocab.find(id);
        if (it == tok.id2vocab.end()) continue;
        int len = (int)it->second.size();
        f.write(reinterpret_cast<const char*>(&id),  sizeof(int));
        f.write(reinterpret_cast<const char*>(&len), sizeof(int));
        f.write(it->second.c_str(), len);
    }
    int nm = (int)tok.merges.size();
    f.write(reinterpret_cast<const char*>(&nm), sizeof(int));
    for (auto& [a, b] : tok.merges) {
        f.write(reinterpret_cast<const char*>(&a), sizeof(int));
        f.write(reinterpret_cast<const char*>(&b), sizeof(int));
    }
}

bool load_bpe(BPETokenizer& tok, const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f.is_open()) return false;
    f.read(reinterpret_cast<char*>(&tok.vocab_size), sizeof(int));
    for (int i = 0; i < tok.vocab_size; ++i) {
        int id, len;
        f.read(reinterpret_cast<char*>(&id),  sizeof(int));
        f.read(reinterpret_cast<char*>(&len), sizeof(int));
        std::string s(len, '\0');
        f.read(&s[0], len);
        tok.id2vocab[id] = s;
        tok.vocab2id[s]  = id;
    }
    int nm;
    f.read(reinterpret_cast<char*>(&nm), sizeof(int));
    for (int i = 0; i < nm; ++i) {
        int a, b;
        f.read(reinterpret_cast<char*>(&a), sizeof(int));
        f.read(reinterpret_cast<char*>(&b), sizeof(int));
        tok.merges.push_back({a, b});
    }
    return !f.fail();
}

// ── Dataset helper ───────────────────────────────────────────
std::string load_text_file(const std::string& path, int max_chars = 2000000) {
    std::ifstream f(path);
    if (!f.is_open()) return "";
    std::stringstream buf; buf << f.rdbuf();
    std::string t = buf.str();
    if ((int)t.size() > max_chars) t = t.substr(0, max_chars);
    return t;
}

// ── Greedy/Sampled generation ──────────────────────────────
std::vector<int> generate_greedy(MiniGPT& model, BPETokenizer& tok,
                                  const std::string& seed, int steps,
                                  int block_size, bool stream = false,
                                  float temperature = 0.0f) {
    std::vector<int> ctx = tok.encode(seed);
    std::vector<int> all = ctx;

    // Use time-based seed so each call produces different output
    auto seed_val = (uint32_t)std::chrono::steady_clock::now()
                    .time_since_epoch().count();
    std::mt19937 rng(seed_val);

    for (int step = 0; step < steps; ++step) {
        int cs = (int)ctx.size() > block_size ? (int)ctx.size() - block_size : 0;
        std::vector<int> c(ctx.begin() + cs, ctx.end());
        if (c.empty()) break;
        auto logits = model.forward(c);
        int T = (int)c.size(), V = tok.vocab_size;

        int best = 0;
        if (temperature <= 0.0f) {
            // Pure greedy (argmax)
            float bv = logits->data[(T-1)*V];
            for (int j = 1; j < V; ++j)
                if (logits->data[(T-1)*V+j] > bv) { bv = logits->data[(T-1)*V+j]; best = j; }
        } else {
            // Temperature sampling — more varied output
            std::vector<float> probs(V);
            float max_l = logits->data[(T-1)*V];
            for (int j = 1; j < V; ++j)
                max_l = std::max(max_l, logits->data[(T-1)*V+j]);
            float sum = 0.0f;
            for (int j = 0; j < V; ++j) {
                probs[j] = std::exp((logits->data[(T-1)*V+j] - max_l) / temperature);
                sum += probs[j];
            }
            for (int j = 0; j < V; ++j) probs[j] /= sum;
            std::discrete_distribution<int> dist(probs.begin(), probs.end());
            best = dist(rng);
        }

        ctx.push_back(best); all.push_back(best);

        if (stream) {
            // Escape \n and \r so line-based SSE parsing is not broken
            const std::string& tok_str = tok.id2vocab.at(best);
            std::string escaped;
            escaped.reserve(tok_str.size() + 4);
            for (char ch : tok_str) {
                if      (ch == '\n') escaped += "\\n";
                else if (ch == '\r') escaped += "\\r";
                else                 escaped += ch;
            }
            std::cout << "TOKEN:" << escaped << "\n" << std::flush;
        }
    }
    return all;
}

int main(int argc, char* argv[]) {
    // ── CLI args ─────────────────────────────────────────────
    bool gen_mode = false;
    std::string seed_arg = "First Citizen:\n";
    for (int i = 1; i < argc; ++i)
        if (std::string(argv[i]) == "--generate" && i+1 < argc)
            { gen_mode = true; seed_arg = argv[++i]; }

    // ── Constants ────────────────────────────────────────────
    const int embed_dim = 64, num_heads = 4, num_layers = 2, block_size = 64;
    const std::string W_PATH = "model.bin", B_PATH = "tokenizer.bin";

    // ============================================================
    // GENERATE MODE
    // ============================================================
    if (gen_mode) {
        BPETokenizer tok;
        bool tok_ok = load_bpe(tok, B_PATH);

        auto do_train = [&]() -> MiniGPT {
            std::string text = load_text_file("dataset.txt");
            if (text.empty()) text = "hello world. to be or not to be. the cat sat on the mat.";
            if (!tok_ok) { tok.train(text, 500); save_bpe(tok, B_PATH); tok_ok = true; }
            MiniGPT m(tok.vocab_size, embed_dim, num_heads, num_layers, block_size);
            AdamW opt(m.parameters(), 1e-3f);
            auto data = tok.encode(text);
            std::mt19937 rng(42);
            std::uniform_int_distribution<int> dist(0, (int)data.size()-block_size-2);
            for (int ep = 0; ep < 5000; ++ep) {
                int s = dist(rng);
                std::vector<int> x(data.begin()+s, data.begin()+s+block_size);
                std::vector<int> y(data.begin()+s+1, data.begin()+s+block_size+1);
                auto loss = Tensor::cross_entropy(m.forward(x), y);
                opt.zero_grad(); loss->backward(); opt.step();
            }
            save_weights(m.parameters(), W_PATH);
            return m;
        };

        if (!tok_ok) {
            std::cout << "STATUS:First run — training (~10s)...\n" << std::flush;
            auto m = do_train();
            std::cout << "STATUS:Ready\n" << std::flush;
            generate_greedy(m, tok, seed_arg, 60, block_size, true, 0.0f);
        } else {
            MiniGPT model(tok.vocab_size, embed_dim, num_heads, num_layers, block_size);
            if (!load_weights(model.parameters(), W_PATH)) {
                std::cout << "STATUS:Re-training...\n" << std::flush;
                auto m = do_train();
                std::cout << "STATUS:Ready\n" << std::flush;
                generate_greedy(m, tok, seed_arg, 60, block_size, true, 0.0f);
            } else {
                std::cout << "STATUS:Ready\n" << std::flush;
                generate_greedy(model, tok, seed_arg, 60, block_size, true, 0.0f);
            }
        }
        return 0;
    }

    // ============================================================
    // TRAIN MODE  (Dashboard ▶ button)
    // ============================================================
    std::cout << "=== Aura Core: Phase 11 — Scaling Up ===\n\n";
    std::string text = load_text_file("dataset.txt");
    if (text.empty()) { std::cerr << "XETA: dataset.txt yoxdur!\n"; return 1; }
    std::cout << "Read " << text.size() << " chars from dataset.\n";

    BPETokenizer tok;
    if (load_bpe(tok, B_PATH)) {
        std::cout << "Loaded existing BPE tokenizer from " << B_PATH << "\n" << std::flush;
    } else {
        std::cout << "Training BPE (500 merges)...\n" << std::flush;
        tok.train(text, 500);
        save_bpe(tok, B_PATH);
    }
    
    auto data = tok.encode(text);
    int vocab_size = tok.vocab_size, data_len = (int)data.size();
    std::cout << "Vocabulary size : " << vocab_size << " subwords\n";
    std::cout << "Dataset length  : " << data_len   << " tokens\n\n";

    MiniGPT model(vocab_size, embed_dim, num_heads, num_layers, block_size);
    
    bool loaded_weights = load_weights(model.parameters(), W_PATH);
    if (loaded_weights) {
        std::cout << "Loaded existing weights from " << W_PATH << ". Resuming training...\n" << std::flush;
    } else {
        std::cout << "No pre-existing weights found. Starting training from scratch with random initialization.\n" << std::flush;
    }

    AdamW optim(model.parameters(), 1e-3f);
    int total_params = 0;
    for (auto& p : model.parameters()) total_params += p->size;
    std::cout << "Model parameters: " << total_params << "\n\n";

    std::mt19937 rng(1337);
    std::uniform_int_distribution<int> dist(0, data_len - block_size - 2);
    std::cout << "Training for 20000 epochs (this will take a few minutes)...\n";
    float initial_loss = -1.0f;
    float running_loss = -1.0f;

    auto t_start = std::chrono::high_resolution_clock::now();
    for (int epoch = 1; epoch <= 20000; ++epoch) {
        int s = dist(rng);
        std::vector<int> x(data.begin()+s, data.begin()+s+block_size);
        std::vector<int> y(data.begin()+s+1, data.begin()+s+block_size+1);
        auto loss = Tensor::cross_entropy(model.forward(x), y);
        optim.zero_grad(); loss->backward(); optim.step();
        float current_loss = loss->data[0];
        
        if (epoch == 1) initial_loss = current_loss;
        
        if (running_loss < 0.0f) {
            running_loss = current_loss;
        } else {
            running_loss = 0.99f * running_loss + 0.01f * current_loss;
        }
        
        if (epoch == 1 || epoch % 50 == 0) {
            auto t_now = std::chrono::high_resolution_clock::now();
            double elapsed = std::chrono::duration<double>(t_now - t_start).count();
            std::cout << "  Epoch " << epoch << " | Batch Loss: " << current_loss << " | Running Loss: " << running_loss;
            if (epoch == 1) {
                std::cout << "  <- baslangiс\n" << std::flush;
            } else {
                std::cout << " | Time: " << elapsed << "s (" << (elapsed / epoch) * 1000.0 << " ms/epoch)\n" << std::flush;
            }
            
            // Save checkpoint weights and tokenizer (only every 1000 epochs to avoid disk I/O bottlenecks)
            if (epoch % 1000 == 0) {
                save_weights(model.parameters(), W_PATH);
                save_bpe(tok, B_PATH);
            }
        }
        
        // Early stopping if running average loss has converged (running_loss < 0.08) after sufficient epochs
        if (epoch >= 6000 && running_loss < 0.08f) {
            std::cout << "  Early stopping triggered at Epoch " << epoch << " | Running Loss: " << running_loss << "\n" << std::flush;
            break;
        }
    }

    save_weights(model.parameters(), W_PATH);
    save_bpe(tok, B_PATH);
    std::cout << "\nSaved -> model.bin + tokenizer.bin\n";
    std::cout << "Chat rejimi indi istifadeye hazirdir!\n\n";

    auto gen_ids = generate_greedy(model, tok, "[USER] Salam\n[AURA] ", 50, block_size);
    std::cout << "--- Generasiya ---\n" << tok.decode(gen_ids) << "\n\n";

    {
        int s = dist(rng);
        std::vector<int> x(data.begin()+s, data.begin()+s+block_size);
        std::vector<int> y(data.begin()+s+1, data.begin()+s+block_size+1);
        auto fl = Tensor::cross_entropy(model.forward(x), y);
        std::cout << "Baslangiс loss: " << initial_loss << "\n";
        std::cout << "Son loss:       " << fl->data[0] << "\n";
        if (fl->data[0] < initial_loss) std::cout << "UGURLU: Model oyreniri!\n";
    }

    std::cout << "\n=== Merhele 11 tamamlandi! ===\n";
    return 0;
}
