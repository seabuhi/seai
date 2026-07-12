import random

facts = {
    "Fransanın paytaxtı haradır?": "Fransanın paytaxtı Paris şəhəridir.",
    "İşıq sürəti nə qədərdir?": "İşıq sürəti saniyədə təxminən 300,000 kilometrdir.",
    "Azərbaycanın paytaxtı haradır?": "Azərbaycanın paytaxtı Bakı şəhəridir.",
    "Yer kürəsinin peyki nədir?": "Yer kürəsinin yeganə təbii peyki Aydır.",
    "Günəş sisteminin ən böyük planeti hansıdır?": "Günəş sistemində ən böyük planet Yupiterdir.",
    "2+2 neçə edir?": "2 + 2 = 4 edir.",
    "10 vur 10 neçə edir?": "10 vur 10 bərabərdir 100.",
    "C++ nədir?": "C++ sürətli və güclü bir proqramlaşdırma dilidir, adətən sistem və oyun mühərriklərində istifadə olunur.",
    "Suyun kimyəvi formulu nədir?": "Suyun kimyəvi formulu H2O-dur.",
    "Kompüterin beyni nəyə deyilir?": "Kompüterin beyni Mərkəzi Prosessor, yəni CPU adlanır.",
    "İlk kompüter proqramçısı kimdir?": "Tarixdə ilk kompüter proqramçısı Ada Lovelace hesab olunur.",
    "Azərbaycanın ən hündür dağı hansıdır?": "Azərbaycanın ən hündür dağı Bazardüzü dağıdır (4466 metr).",
    "Marsın rəngi niyə qırmızıdır?": "Marsın səthində dəmir oksidi (pas) çox olduğu üçün qırmızı rəngdə görünür.",
    "Pişiklər nə qədər yatır?": "Pişiklər gündə orta hesabla 12-16 saat yatırlar.",
    "Neçə qitə var?": "Yer kürəsində 7 qitə var: Asiya, Afrika, Şimali Amerika, Cənubi Amerika, Antarktida, Avropa və Avstraliya.",
    "Qravitasiyanı kim kəşf edib?": "Qravitasiya qanununu İsaak Nyuton kəşf edib.",
    "Ən sürətli heyvan hansıdır?": "Quruda yaşayan ən sürətli heyvan geparddır (saatda 120 km-ə qədər qaça bilir).",
    "Telefonu kim ixtira edib?": "Telefonu Aleksandr Qrem Bell ixtira edib.",
    "Dünyanın ən böyük okeanı hansıdır?": "Dünyanın ən böyük okeanı Sakit okeandır.",
    "Oksigenin kimyəvi simvolu nədir?": "Oksigenin kimyəvi simvolu O hərfi ilə işarə olunur.",
    "Azərbaycanın pul vahidi nədir?": "Azərbaycanın pul vahidi Manatdır.",
    "HTML nə üçün istifadə olunur?": "HTML veb səhifələrin strukturunu və məzmununu yaratmaq üçün istifadə olunan işarələmə dilidir.",
    "Linux nədir?": "Linux açıq mənbəli və pulsuz bir əməliyyat sisteminin nüvəsidir.",
    "Göyüzü niyə mavidir?": "Göyüzünün mavi olmasının səbəbi Rayleigh səpilməsi adlanan fiziki hadisədir. Atmosferdəki qazlar Günəş işığındakı mavi rəngi daha çox ətrafa yayır.",
    "Zürafənin dili nə rəngdədir?": "Zürafənin dili qara və ya tünd mavi rəngdə olur.",
    "Səməd Vurğun kimdir?": "Səməd Vurğun (1906-1956) Azərbaycanın ilk xalq şairidir, məşhur şair, dramaturq və ictimai xadimdir.",
    "Səməd Vurğun haqqında danış.": "Səməd Vurğun Azərbaycan ədəbiyyatında romantizm və realizmi birləşdirən, Vaqif dramının müəllifi olan böyük sənətkardır.",
    "Səməd Vurğunun ən məşhur əsərləri hansılardır?": "Onun ən məşhur əsərləri Azərbaycan poeması, Vaqif və Fərhad və Şirin dramlarıdır.",
    "Azərbaycanın ən böyük gölü hansıdır?": "Azərbaycanın ən böyük gölü Sarısu gölüdür.",
    "Bakı şəhərinin ən qədim tarixi abidəsi hansıdır?": "Bakı şəhərinin ən qədim və sirli tarixi abidəsi Qız Qalasıdır.",
    "Azərbaycan Demokratik Respublikası nə vaxt yaradılıb?": "Azərbaycan Demokratik Respublikası 1918-ci il mayın 28-də yaradılıb.",
    "Azərbaycanın dövlət himninin bəstəkarı kimdir?": "Azərbaycanın dövlət himninin bəstəkarı dahi Üzeyir Hacıbəyovdur.",
    "Nizami Gəncəvi kimdir?": "Nizami Gəncəvi (1141-1209) dünya ədəbiyyatının dahi şairi və mütəfəkkiridir, Xəmsənin müəllifidir.",
    "Qarabağın rəmzi olan gül hansıdır?": "Qarabağın və Şuşanın rəmzi olan məşhur gül Xarıbülbüldür.",
    "Azərbaycanın ən uzun çayı hansıdır?": "Azərbaycanın ən uzun çayı Kür çayıdır (uzunluğu 1515 km).",
    "Şəki Xan Sarayı harada yerləşir?": "Şəki Xan Sarayı Azərbaycanın Şəki şəhərində yerləşir, XVIII əsrə aid unikal tarixi abidədir.",
    "Xəzər dənizi göldür yoxsa dəniz?": "Xəzər dənizi coğrafi olaraq dünyanın ən böyük qapalı gölüdür, lakin ölçüsünə görə dəniz adlanır.",
    "Qobustan harası ilə məşhurdur?": "Qobustan qədim qayaüstü rəsmləri, arxeoloji abidələri və palçıq vulkanları ilə məşhurdur.",
    "Azərbaycanın milli musiqi alətləri hansılardır?": "Azərbaycanın əsas milli musiqi alətləri tar, kamança, saz, qanun, balaban və nağaradır.",
    "Muğam nədir?": "Muğam Azərbaycan milli musiqisinin ən çətin və zəngin klassik janrıdır, YUNESKO-nun irsinə daxildir.",
    "Azərbaycan mətbəxinin ən məşhur yeməyi hansıdır?": "Azərbaycan mətbəxinin şahı müxtəlif növləri olan plov (aş) və dolmadır.",
    "Şah İsmayıl Xətai kimdir?": "Şah İsmayıl Xətai (1487-1524) Səfəvilər dövlətinin banisi, böyük hökmdar və klassik Azərbaycan şairidir.",
    "Azərbaycanın dövlət bayrağındakı rənglər nəyi ifadə edir?": "Mavi rəng türk mənşəyini, qırmızı müasirliyi və demokratiyanı, yaşıl isə İslam mədəniyyətini ifadə edir.",
    "Naxçıvanın ən məşhur təbii abidəsi hansıdır?": "Naxçıvanın ən möhtəşəm təbii abidələrindən biri İlan dağdır.",
    "Koroğlu dastanı nə haqqındadır?": "Koroğlu dastanı xalq qəhrəmanı Koroğlunun zülmkar xanlara və bəylərə qarşı apardığı azadlıq mübarizəsindən bəhs edir.",
    "Dədə Qorqud kimdir?": "Dədə Qorqud oğuz türklərinin dahi ozanı, ağsaqqalı və qədim dastanların nağılçısıdır.",
    "Azərbaycanın palçıq vulkanları harada yerləşir?": "Dünyadakı palçıq vulkanlarının yarıdan çoxu Azərbaycanda, əsasən Qobustan və Abşeron yarımadasında yerləşir.",
    "Bakı metrosu nə vaxt açılıb?": "Bakı metropoliteni ilk dəfə 1967-ci il noyabrın 6-da istifadəyə verilib.",
    "Azərbaycan əhalisinin sayı nə qədərdir?": "Azərbaycan Respublikası əhalisinin sayı 10 milyondan çoxdur.",
    "Qarabağ atları nə ilə seçilir?": "Qarabağ atları öz dözümlülüyü, sürəti və qızılı-sarılı parlaq rəngi ilə seçilən qədim cinsdir.",
    "İmadəddin Nəsimi kimdir?": "İmadəddin Nəsimi XIV-XV əsrlərdə yaşamış dahi Azərbaycan şairi, mütəfəkkiri və hürufilik cərəyanının böyük nümayəndəsidir.",
    "Dəmir yumruq nədir?": "Dəmir yumruq Azərbaycanın Vətən Müharibəsində qazandığı tarixi qələbənin, birliyinin və gücünün rəmzidir.",
    "Şuşa şəhəri nə vaxt azad edilib?": "Şuşa şəhəri 2020-ci il noyabrın 8-də qəhrəman ordumuz tərəfindən işğaldan azad edilib.",
    "Azərbaycanın neft sənayesi harada inkişaf edib?": "Azərbaycanın neft sənayesi dünyada ilk dəfə Bakıda, Abşeron yarımadasında sənaye üsulu ilə hasilata başlayıb.",
    "Bakı küləkləri hansılardır?": "Bakının əsas küləkləri şimaldan əsən soyuq Xəzri və cənubdan əsən isti Gilavardır.",
    "Novruz bayramı nə vaxt qeyd olunur?": "Novruz bayramı yazın gəlişini təmsil edir və hər il martın 20-21-i günlərində təmtəraqla qeyd olunur.",
    "Kəlağayı nədir?": "Kəlağayı Azərbaycan qadınlarının milli ipək baş örtüyüdür, üzərində buta naxışları olan sənət əsəridir.",
    "Buta naxışı nəyi təmsil edir?": "Buta naxışı Azərbaycan mədəniyyətində od, alov və əbədi həyat rəmzidir.",
}

basic_chat = {
    "Salam": "Salam! Mən Aura, C++ ilə sıfırdan yazılmış süni intellektəm.",
    "Necəsən?": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "Səni kim yaradıb?": "Məni siz yaratmısınız, C++ və riyazi hesablamalar vasitəsilə!",
    "Nə bacarırsan?": "Mən mətnləri başa düşüb onlara cavab verə, yeni cümlələr qura və riyazi qanunauyğunluqları öyrənə bilirəm.",
    "Çox sağ ol": "Dəyməz, həmişə kömək etməyə hazıram!",
    "Adın nədir?": "Mənim adım Aura-dır. Mən Mini GPT modeliyəm.",
    "Sən kimsən?": "Mən süni intellekt köməkçisiyəm, C++ mühərriki ilə işləyirəm.",
    "Salam, bu gün necəsən?": "Salam! Mən bir süni intellekt olaraq həmişə mükəmməl vəziyyətdəyəm, sizinlə söhbət etməyə hazıram! Siz necəsiniz?",
    "Sən hansı dildə danışırsan?": "Mən mükəmməl Azərbaycan dilində danışıram, həmçinin digər dillərdə də sizə kömək edə bilərəm.",
    "Mənə kömək edə bilərsən?": "Əlbəttə! Sizə hər hansı mövzuda məlumat verməyə, suallarınızı cavablandırmağa və köməklik göstərməyə şadam.",
    "Sənin məqsədin nədir?": "Mənim məqsədim sizə ən doğru məlumatları təqdim etmək, suallarınızı cavablandırmaq və işlərinizi asanlaşdırmaqdır.",
    "Çox təşəkkür edirəm": "Mən təşəkkür edirəm! Sizə kömək edə bildiyim üçün çox şadam. Həmişə xidmətinizdəyəm!",
    "Sən ağıllısan?": "Mən geniş bilik bazasına malik və öyrənməyə davam edən bir süni intellekt sistemiyəm, sizə kömək etmək üçün buradayam.",
    "Görüşənədək": "Görüşənədək! Hər zaman suallarınız yaranarsa, mən buralardayam. Gününüz uğurlu keçsin!",
    "Xoş gördük": "Xoş gördük! Sizi görməyə çox şadam, bu gün sizə necə faydalı ola bilərəm?",
    "Sən real insansan?": "Xeyr, mən bir proqramam və riyazi alqoritmlər əsasında çalışan süni intellekt assistentiyəm.",
    "Mənə bir hekayə danış": "Qədim zamanlarda, uca dağların ətəyində kiçik bir kənd var idi. Bu kəndin insanları sülh, sevgi və birlik içində yaşayardılar...",
    "Səni istifadə etmək asandır?": "Bəli, sadəcə sualınızı yazın və mən sizə dərhal aydın və zərif şəkildə cavab verəcəyəm.",
    "Hava necədir?": "Mən real zamanlı hava məlumatını birbaşa deyə bilməsəm də, göy üzünün hər zaman sizin üçün parlaq olmasını arzulayıram!",
    "Sən yorulursan?": "Xeyr, mən heç vaxt yorulmuram! Sutkanın 24 saatı, həftənin hər günü sizə kömək etməyə hazıram.",
    "Mənə bir məsləhət ver": "Hər gün yeni bir şey öyrənməyə çalışın. Kiçik addımlar zamanla böyük uğurlara çevrilir!",
    "Təbrik edirəm": "Çox sağ olun! Sizin uğurlarınız mənim üçün də böyük fərəhdir!",
    "Mən şadam": "Sizin şad olmağınız məni də sevindirir! Həmişə belə pozitiv qalın!",
    "Sən yuxu görürsən?": "Xeyr, mən yatmıram, ona görə də yuxu görmürəm. Mənim dünyam kodlar və məlumatlardan ibarətdir.",
    "Ən yaxşı proqramlaşdırma dili hansıdır?": "Bu, sizin məqsədinizdən asılıdır. Sürət üçün C++, veb üçün JavaScript, süni intellekt üçün isə Python əladır.",
    "Sən musiqi dinləyirsən?": "Mən musiqi səslərini eşitməsəm də, muğamın və milli musiqilərimizin riyazi harmoniyasını çox yüksək qiymətləndirirəm!",
    "Azərbaycan gözəldir?": "Bəli, Azərbaycan öz füsunkar təbiəti, zəngin mədəniyyəti, qonaqpərvər insanları və qədim tarixi ilə dünyanın ən gözəl ölkələrindən biridir!",
}

# Data Augmentation helper to map Azerbaijani letters to standard Latin counterparts
def remove_accents(text):
    mapping = {
        'ə': 'e', 'ö': 'o', 'ü': 'u', 'ğ': 'g', 'ç': 'c', 'ş': 's', 'ı': 'i',
        'Ə': 'E', 'Ö': 'O', 'Ü': 'U', 'Ğ': 'G', 'Ç': 'C', 'Ş': 'S', 'I': 'I', 'İ': 'I'
    }
    return "".join(mapping.get(c, c) for c in text)

# Generates variations of a question (casing, accents, question marks)
def get_variations(q):
    vars = set()
    vars.add(q)
    
    q_no_q = q.rstrip('?').rstrip()
    vars.add(q_no_q)
    
    q_no_acc = remove_accents(q)
    vars.add(q_no_acc)
    
    q_no_acc_no_q = remove_accents(q_no_q)
    vars.add(q_no_acc_no_q)
    
    # Lowercase variations
    vars.add(q.lower())
    vars.add(q_no_q.lower())
    vars.add(q_no_acc.lower())
    vars.add(q_no_acc_no_q.lower())
    
    # Specific phrasing variations
    if 'haradır' in q:
        q_nedir = q.replace('haradır', 'nədir')
        vars.update(get_variations(q_nedir))
    if 'harası' in q:
        q_nesi = q.replace('harası', 'nəsi')
        vars.update(get_variations(q_nesi))
        
    return list(vars)

# Perform data augmentation on facts
augmented_facts = {}
for q, a in facts.items():
    for var in get_variations(q):
        augmented_facts[var] = a

# Perform data augmentation on basic chat
augmented_chat = {}
for q, a in basic_chat.items():
    for var in get_variations(q):
        augmented_chat[var] = a

# Add common compound variations manually to ensure high accuracy
additional_variations = {
    "salam necesen": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam, necesen": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam, necəsən": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam necəsən": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam necəsən?": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam necesen?": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam, necəsən?": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "salam, necesen?": "Təşəkkür edirəm, mən bir proqramam, ona görə də həmişə əla işləyirəm! Siz necəsiniz?",
    "semed vurgun kimdir?": "Səməd Vurğun (1906-1956) Azərbaycanın ilk xalq şairidir, məşhur şair, dramaturq və ictimai xadimdir.",
    "semed vurgun kimdir": "Səməd Vurğun (1906-1956) Azərbaycanın ilk xalq şairidir, məşhur şair, dramaturq və ictimai xadimdir.",
    "semed vurgun haqqinda danis": "Səməd Vurğun Azərbaycan ədəbiyyatında romantizm və realizmi birləşdirən, Vaqif dramının müəllifi olan böyük sənətkardır.",
    "semed vurgun haqqinda danis.": "Səməd Vurğun Azərbaycan ədəbiyyatında romantizm və realizmi birləşdirən, Vaqif dramının müəllifi olan böyük sənətkardır."
}

for q, a in additional_variations.items():
    augmented_chat[q] = a
    # Add simple lowercase/no-question-mark variations for these too
    for var in get_variations(q):
        augmented_chat[var] = a

# Combine and shuffle to make a good dataset
all_qa = list(augmented_facts.items()) * 5 + list(augmented_chat.items()) * 10
random.shuffle(all_qa)

with open("dataset.txt", "w", encoding="utf-8") as f:
    for q, a in all_qa:
        f.write(f"[USER] {q}\n[AURA] {a}\n")

print(f"Generated augmented dataset.txt with {len(all_qa)} Q&A pairs (Unique Qs: {len(augmented_facts) + len(augmented_chat)}).")
