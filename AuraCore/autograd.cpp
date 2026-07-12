#include <iostream>
#include <vector>
#include <memory>
#include <cmath>
#include <functional>
#include <algorithm>

// Minimal Autograd Engine for Aura AI
class Value : public std::enable_shared_from_this<Value> {
public:
    float data;
    float grad;
    std::vector<std::shared_ptr<Value>> prev;
    std::function<void()> _backward;

    Value(float d, std::vector<std::shared_ptr<Value>> p = {}) : data(d), grad(0), prev(p) {
        _backward = []() {};
    }

    static std::shared_ptr<Value> make(float d, std::vector<std::shared_ptr<Value>> p = {}) {
        return std::make_shared<Value>(d, p);
    }

    std::shared_ptr<Value> operator+(std::shared_ptr<Value> other) {
        auto out = Value::make(data + other->data, {shared_from_this(), other});
        out->_backward = [self = shared_from_this(), other, out]() {
            self->grad += out->grad;
            other->grad += out->grad;
        };
        return out;
    }

    std::shared_ptr<Value> operator*(std::shared_ptr<Value> other) {
        auto out = Value::make(data * other->data, {shared_from_this(), other});
        out->_backward = [self = shared_from_this(), other, out]() {
            self->grad += other->data * out->grad;
            other->grad += self->data * out->grad;
        };
        return out;
    }

    void backward() {
        std::vector<std::shared_ptr<Value>> topo;
        std::vector<std::shared_ptr<Value>> visited;

        std::function<void(std::shared_ptr<Value>)> build_topo = [&](std::shared_ptr<Value> v) {
            if (std::find(visited.begin(), visited.end(), v) == visited.end()) {
                visited.push_back(v);
                for (auto p : v->prev) build_topo(p);
                topo.push_back(v);
            }
        };

        build_topo(shared_from_this());
        grad = 1.0f;
        std::reverse(topo.begin(), topo.end());
        for (auto v : topo) v->_backward();
    }
};

int main() {
    std::cout << "Aura Autograd Test:\n";
    auto x = Value::make(2.0f);
    auto y = Value::make(-3.0f);
    auto z = (x * y) + Value::make(10.0f);

    z->backward();

    std::cout << "x grad (expected -3.0): " << x->grad << "\n";
    std::cout << "y grad (expected 2.0): " << y->grad << "\n";
    std::cout << "z data (expected 4.0): " << z->data << "\n";

    return 0;
}
