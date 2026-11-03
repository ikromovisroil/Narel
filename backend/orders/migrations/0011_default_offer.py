from django.db import migrations

# Narel ommaviy ofertasining boshlang'ich matni. Admin -> Sozlamalar -> "Ommaviy oferta" da tahrirlanadi.
# "# " bilan boshlangan qator — bo'lim sarlavhasi. [Kvadrat qavs] ichidagilarni kompaniya ma'lumotlari bilan almashtiring.

OFFER_UZ = """Ushbu hujjat [MChJ nomi] (keyingi o'rinlarda — Sotuvchi) tomonidan Narel internet-do'koni orqali tovarlarni masofadan sotish shartlarini belgilaydi va O'zbekiston Respublikasi Fuqarolik kodeksiga muvofiq ommaviy oferta hisoblanadi. Buyurtmani rasmiylashtirgan har qanday shaxs ushbu shartlarni to'liq qabul qilgan hisoblanadi.

# 1. Atamalar
1.1. Sotuvchi — [MChJ nomi], ushbu ofertaning 14-bo'limida ko'rsatilgan rekvizitlar bilan.
1.2. Xaridor — internet-do'kondan shaxsiy, oilaviy yoki boshqa tadbirkorlikka bog'liq bo'lmagan maqsadlarda tovar xarid qiluvchi jismoniy shaxs.
1.3. Internet-do'kon (Sayt) — Sotuvchiga tegishli Narel sayti va uning barcha sahifalari.
1.4. Tovar — Saytda tavsifi, narxi va rasmi bilan e'lon qilingan mahsulot.
1.5. Buyurtma — Xaridorning Saytda tanlangan tovarlarni sotib olish to'g'risidagi rasmiylashtirilgan so'rovi.
1.6. Aksept — Xaridorning Saytda buyurtmani rasmiylashtirishi; u ushbu oferta shartlariga to'liq va so'zsiz rozilikni bildiradi.
1.7. Shaxsiy kabinet (Profil) — Xaridorning Saytdagi shaxsiy bo'limi: buyurtmalar tarixi, holati va shaxsiy ma'lumotlar.

# 2. Umumiy qoidalar
2.1. Shartnoma Xaridor buyurtmani rasmiylashtirgan paytdan boshlab tuzilgan hisoblanadi.
2.2. Sotuvchi ofertani bir tomonlama o'zgartirishi mumkin. O'zgarishlar Saytda e'lon qilingan paytdan kuchga kiradi va undan oldin rasmiylashtirilgan buyurtmalarga taalluqli emas.
2.3. Oferta muddatsiz amal qiladi va Saytdan olib tashlangan paytda o'z kuchini yo'qotadi.
2.4. Ushbu ofertada nazarda tutilmagan munosabatlar O'zbekiston Respublikasi qonunchiligi, jumladan "Iste'molchilarning huquqlarini himoya qilish to'g'risida"gi va "Elektron tijorat to'g'risida"gi qonunlar bilan tartibga solinadi.

# 3. Saytga kirish va Shaxsiy kabinet
3.1. Buyurtma berish uchun Xaridor Saytga telefon raqami orqali kiradi: ko'rsatilgan raqamga bir martalik SMS kod yuboriladi. Raqam birinchi marta kiritilganda Shaxsiy kabinet avtomatik ochiladi. Saytga Google yoki Apple hisobi orqali ham kirish mumkin.
3.2. SMS kod 2 daqiqa amal qiladi. Kodni uchinchi shaxslarga berish taqiqlanadi. Kod orqali Shaxsiy kabinetda bajarilgan barcha harakatlar Xaridorning o'zi tomonidan bajarilgan deb hisoblanadi.
3.3. Xaridor o'z telefon raqami va hisobining xavfsizligi uchun javobgar. Raqam boshqa shaxsga o'tganda yoki yo'qolganda Xaridor Profilda raqamni o'zgartirishi yoki Sotuvchiga murojaat qilishi kerak.
3.4. Xaridor Profilda ism, familiya, telefon va yetkazish manzilini ko'rsatadi va ularning to'g'riligi uchun javob beradi. Noto'g'ri ma'lumot sababli yetkazishdagi kechikishlar uchun Sotuvchi javobgar emas.

# 4. Tovar va narxlar
4.1. Tovar narxlari Saytda so'mda ko'rsatiladi va barcha soliqlarni o'z ichiga oladi. Yetkazib berish narxi alohida ko'rsatiladi.
4.2. Sotuvchi narxlarni bir tomonlama o'zgartirishi mumkin. Rasmiylashtirilgan buyurtma narxi o'zgarmaydi.
4.3. Saytdagi tovar rasmlari va tavsiflari ma'lumot uchun berilgan; tovarning rangi, qadoqlanishi yoki tashqi ko'rinishi ishlab chiqaruvchi tomonidan uning iste'mol xususiyatlariga ta'sir qilmagan holda o'zgartirilishi mumkin.
4.4. Saytda texnik xato tufayli tovar narxi aniq noto'g'ri ko'rsatilgan bo'lsa, Sotuvchi Xaridorga bu haqda xabar beradi; Xaridor buyurtmani to'g'ri narxda tasdiqlashi yoki bekor qilishi mumkin.

# 5. Buyurtmani rasmiylashtirish
5.1. Xaridor tovarlarni savatga qo'shadi, yetkazish usulini (kuryer orqali yoki filialdan olib ketish) va to'lov usulini tanlaydi hamda buyurtmani tasdiqlaydi.
5.2. Buyurtma qabul qilingach, u "Qabul qilindi" holatini oladi. Sotuvchi operatori zarurat bo'lsa Xaridor bilan bog'lanib, buyurtmani aniqlashtiradi.
5.3. Buyurtma holati (qabul qilindi, tasdiqlandi, yo'lda / olib ketishga tayyor, yetkazildi / topshirildi, bekor qilindi) Shaxsiy kabinetdagi "Buyurtmalarim" bo'limida ko'rsatiladi.
5.4. Tovar omborda qolmagan yoki boshqa sabab bilan buyurtmani bajarishning imkoni bo'lmasa, Sotuvchi Xaridorni xabardor qilib buyurtmani bekor qilishi mumkin. Bunday holda to'langan summa 9-bo'limda ko'rsatilgan tartibda to'liq qaytariladi.
5.5. Xaridor buyurtmani u "Yo'lda" holatiga o'tgunga qadar bepul bekor qilishi mumkin.

# 6. Yetkazib berish va olib ketish
6.1. Kuryer orqali yetkazishda narx va taxminiy muddat Saytda buyurtma berish paytida ko'rsatiladi. Aniq yetkazish sanasi buyurtma tasdiqlanganda belgilanadi va Shaxsiy kabinetda ko'rinadi.
6.2. Sotuvchiga bog'liq bo'lmagan sabablarga ko'ra (ob-havo, yo'l holati, ishlab chiqaruvchidan kechikish va h.k.) muddat o'zgarishi mumkin. Bunday holda Sotuvchi Xaridorni Shaxsiy kabinet orqali xabardor qiladi va yangi sanani ko'rsatadi.
6.3. Do'kondan olib ketishda Xaridor buyurtma berishda filialni tanlaydi. Buyurtma "Olib ketishga tayyor" holatiga o'tgach, Xaridor uni filialning ish vaqtida olib ketishi mumkin. Tovar [7] kun davomida saqlanadi, so'ng buyurtma bekor qilinishi mumkin.
6.4. Tovarni qabul qilishda Xaridor uning tashqi ko'rinishi, butligi va to'liqligini tekshiradi. Tashqi nuqsonlar haqidagi e'tirozlar tovar topshirilgan paytda bildiriladi.
6.5. Tovarning tasodifan yo'qolishi yoki shikastlanishi xavfi Xaridorga tovar topshirilgan paytdan o'tadi.

# 7. To'lov
7.1. To'lov Saytda yoqilgan usullardan biri bilan amalga oshiriladi: naqd pul, bank kartasi, Click, Payme, Paynet, Uzum Bank yoki muddatli to'lov. Mavjud usullar buyurtma berish sahifasida ko'rsatiladi.
7.2. Naqd yoki karta bilan to'lov tovar topshirilganda amalga oshiriladi. Onlayn to'lovda buyurtma to'lov tasdiqlangandan keyin bajariladi.
7.3. Muddatli to'lov hamkor bank yoki moliya tashkiloti bilan alohida shartnoma asosida rasmiylashtiriladi; uning shartlari o'sha tashkilot tomonidan belgilanadi.
7.4. Sotuvchi Xaridorga qonunchilikka muvofiq to'lovni tasdiqlovchi hujjat (chek) beradi.

# 8. Sifat va kafolat
8.1. Sotuvchi sertifikatlangan, sifati O'zbekiston Respublikasi talablariga mos tovarlarni sotadi.
8.2. Tovarga ishlab chiqaruvchi yoki Sotuvchi kafolati beriladi; kafolat muddati tovar sahifasida yoki kafolat talonida ko'rsatiladi.
8.3. Kafolat tovarni noto'g'ri ishlatish, mexanik shikastlanish, suyuqlik tushishi, ruxsatsiz ta'mirlash va ishlab chiqaruvchi ko'rsatmalari buzilgan holatlarga tatbiq etilmaydi.
8.4. Kafolat bo'yicha murojaat uchun Xaridor tovarni, chekni va kafolat talonini (bo'lsa) taqdim etadi.

# 9. Qaytarish va almashtirish
9.1. Sifatli tovarni Xaridor qonunchilikda belgilangan tartibda, xarid qilingan kundan boshlab 10 kun ichida qaytarishi yoki almashtirishi mumkin: tovar ishlatilmagan, tovar ko'rinishi, qadoqlari, plombalari, yorliqlari va to'liq jamlanmasi saqlangan bo'lishi hamda chek taqdim etilishi kerak.
9.2. Qonunchilikda belgilangan ro'yxatga kiruvchi tovarlar (jumladan, kafolat muddati belgilangan texnik murakkab maishiy tovarlar) sifatli bo'lsa qaytarilmaydi va almashtirilmaydi, qonunchilikda boshqacha nazarda tutilgan hollar bundan mustasno.
9.3. Nuqsonli tovar aniqlanganda Xaridor qonunchilikka muvofiq tovarni almashtirish, bepul ta'mirlash, narxni mutanosib kamaytirish yoki pulni qaytarishni talab qilishi mumkin. Zarur bo'lsa, tovar tekshiruvdan (ekspertizadan) o'tkaziladi.
9.4. Qaytarilgan tovar uchun pul qaytarish talabi qabul qilingan kundan boshlab qonunchilikda belgilangan muddatda, to'lov qilingan usul bilan (naqd to'lovda — naqd yoki Xaridor ko'rsatgan bank kartasiga) qaytariladi.

# 10. Shaxsiy ma'lumotlar
10.1. Buyurtma berish va Saytdan foydalanish orqali Xaridor "Shaxsga doir ma'lumotlar to'g'risida"gi Qonunga muvofiq o'z shaxsiy ma'lumotlarini (ism, familiya, telefon, manzil, email) qayta ishlashga rozilik beradi.
10.2. Ma'lumotlar faqat buyurtmani bajarish, yetkazib berish, Xaridor bilan bog'lanish va xizmat sifatini oshirish uchun ishlatiladi. Ular faqat buyurtmani bajarish uchun zarur bo'lgan hamkorlarga (yetkazib berish xizmati, to'lov tizimi, SMS xizmati) beriladi.
10.3. Xaridor o'z ma'lumotlarini Profilda istalgan vaqtda o'zgartirishi yoki ularni o'chirishni so'rab Sotuvchiga murojaat qilishi mumkin.

# 11. Firibgarlikning oldini olish
11.1. Shubhali buyurtmalar (masalan, boshqa shaxsning to'lov vositasidan foydalanish, ko'plab bir xil buyurtmalar) aniqlansa, Sotuvchi buyurtmani qo'shimcha tekshirishi, Xaridordan shaxsini tasdiqlashni so'rashi yoki uni bekor qilishi mumkin.
11.2. Sotuvchi o'z nomidan parol yoki SMS kodni hech qachon so'ramaydi. Bunday so'rov kelsa, Xaridor kodni bermasligi va Sotuvchiga xabar berishi kerak.

# 12. Tomonlarning javobgarligi va fors-major
12.1. Tomonlar ofertani bajarmagani yoki lozim darajada bajarmagani uchun qonunchilikka muvofiq javobgar bo'ladi.
12.2. Tomonlar yengib bo'lmaydigan kuch holatlari (tabiiy ofatlar, urush, epidemiya, davlat organlarining qarorlari, aloqa va elektr tarmoqlaridagi uzilishlar va h.k.) sababli majburiyatlarni bajara olmaganlik uchun javobgar emas.
12.3. Sotuvchi tovarni noto'g'ri ishlatish oqibatida yetkazilgan zarar va uchinchi shaxslar xizmatlaridagi (bank, to'lov tizimi, mobil aloqa) uzilishlar uchun javobgar emas.

# 13. Nizolarni hal qilish
13.1. Nizolar avvalo muzokara yo'li bilan hal qilinadi. Xaridor da'vosini telefon yoki email orqali yuborishi mumkin; da'vo qonunchilikda belgilangan muddatda ko'rib chiqiladi.
13.2. Kelishuvga erishilmasa, nizo O'zbekiston Respublikasi qonunchiligiga muvofiq sudda hal qilinadi.

# 14. Sotuvchi rekvizitlari
Nomi: [MChJ nomi]
STIR: [STIR]
Yuridik manzil: [manzil]
Bank: [bank nomi], h/r: [hisob raqami], MFO: [MFO]
Telefon: [telefon]
Email: [email]
Rahbar: [F.I.Sh.]

Tahrir sanasi: 2026-yil 3-noyabr"""

OFFER_RU = """Настоящий документ определяет условия дистанционной продажи товаров [наименование ООО] (далее — Продавец) через интернет-магазин Narel и является публичной офертой в соответствии с Гражданским кодексом Республики Узбекистан. Любое лицо, оформившее заказ, считается полностью принявшим эти условия.

# 1. Термины
1.1. Продавец — [наименование ООО] с реквизитами, указанными в разделе 14 настоящей оферты.
1.2. Покупатель — физическое лицо, приобретающее товар в интернет-магазине для личных, семейных и иных целей, не связанных с предпринимательской деятельностью.
1.3. Интернет-магазин (Сайт) — сайт Narel, принадлежащий Продавцу, и все его страницы.
1.4. Товар — продукция, размещённая на Сайте с описанием, ценой и изображением.
1.5. Заказ — оформленный на Сайте запрос Покупателя на покупку выбранных товаров.
1.6. Акцепт — оформление Покупателем заказа на Сайте, означающее полное и безоговорочное согласие с условиями настоящей оферты.
1.7. Личный кабинет (Профиль) — персональный раздел Покупателя на Сайте: история и статусы заказов, личные данные.

# 2. Общие положения
2.1. Договор считается заключённым с момента оформления Покупателем заказа.
2.2. Продавец вправе изменять оферту в одностороннем порядке. Изменения вступают в силу с момента публикации на Сайте и не распространяются на заказы, оформленные ранее.
2.3. Оферта действует бессрочно и утрачивает силу с момента её удаления с Сайта.
2.4. Отношения, не урегулированные настоящей офертой, регулируются законодательством Республики Узбекистан, в том числе законами «О защите прав потребителей» и «Об электронной коммерции».

# 3. Вход на Сайт и Личный кабинет
3.1. Для оформления заказа Покупатель входит на Сайт по номеру телефона: на указанный номер отправляется одноразовый SMS-код. При первом вводе номера Личный кабинет создаётся автоматически. Войти также можно через аккаунт Google или Apple.
3.2. SMS-код действует 2 минуты. Передавать код третьим лицам запрещено. Все действия в Личном кабинете, совершённые с использованием кода, считаются совершёнными самим Покупателем.
3.3. Покупатель несёт ответственность за безопасность своего номера телефона и аккаунта. При смене или утрате номера Покупатель должен изменить номер в Профиле или обратиться к Продавцу.
3.4. Покупатель указывает в Профиле имя, фамилию, телефон и адрес доставки и отвечает за их достоверность. Продавец не несёт ответственности за задержки доставки из-за неверных данных.

# 4. Товар и цены
4.1. Цены на товары указываются на Сайте в сумах и включают все налоги. Стоимость доставки указывается отдельно.
4.2. Продавец вправе изменять цены в одностороннем порядке. Цена оформленного заказа не меняется.
4.3. Изображения и описания товаров на Сайте носят информационный характер; цвет, упаковка или внешний вид товара могут быть изменены производителем без ухудшения потребительских свойств.
4.4. Если из-за технической ошибки цена товара на Сайте указана явно неверно, Продавец сообщает об этом Покупателю; Покупатель вправе подтвердить заказ по правильной цене или отменить его.

# 5. Оформление заказа
5.1. Покупатель добавляет товары в корзину, выбирает способ получения (курьером или самовывоз из филиала) и способ оплаты и подтверждает заказ.
5.2. После оформления заказ получает статус «Принят». При необходимости оператор Продавца связывается с Покупателем для уточнения заказа.
5.3. Статус заказа (принят, подтверждён, в пути / готов к выдаче, доставлен / выдан, отменён) отображается в разделе «Мои заказы» Личного кабинета.
5.4. Если товара нет на складе или заказ невозможно выполнить по иной причине, Продавец вправе отменить заказ, уведомив Покупателя. В этом случае оплаченная сумма возвращается полностью в порядке, указанном в разделе 9.
5.5. Покупатель может бесплатно отменить заказ до перехода в статус «В пути».

# 6. Доставка и самовывоз
6.1. Стоимость и ориентировочный срок курьерской доставки указываются на Сайте при оформлении заказа. Точная дата доставки устанавливается при подтверждении заказа и отображается в Личном кабинете.
6.2. По причинам, не зависящим от Продавца (погода, дорожная ситуация, задержки производителя и т. п.), срок может измениться. В этом случае Продавец уведомляет Покупателя через Личный кабинет и указывает новую дату.
6.3. При самовывозе Покупатель выбирает филиал при оформлении заказа. После перехода заказа в статус «Готов к выдаче» Покупатель может забрать его в рабочее время филиала. Товар хранится [7] дней, после чего заказ может быть отменён.
6.4. При получении Покупатель проверяет внешний вид, целостность и комплектность товара. Претензии по внешним дефектам заявляются в момент передачи товара.
6.5. Риск случайной гибели или повреждения товара переходит к Покупателю с момента передачи товара.

# 7. Оплата
7.1. Оплата производится одним из включённых на Сайте способов: наличными, банковской картой, через Click, Payme, Paynet, Uzum Bank или в рассрочку. Доступные способы указаны на странице оформления заказа.
7.2. Оплата наличными или картой производится при получении товара. При онлайн-оплате заказ выполняется после подтверждения платежа.
7.3. Рассрочка оформляется по отдельному договору с банком или финансовой организацией-партнёром; её условия устанавливает эта организация.
7.4. Продавец выдаёт Покупателю документ, подтверждающий оплату (чек), в соответствии с законодательством.

# 8. Качество и гарантия
8.1. Продавец реализует сертифицированные товары, качество которых соответствует требованиям Республики Узбекистан.
8.2. На товар предоставляется гарантия производителя или Продавца; гарантийный срок указан на странице товара или в гарантийном талоне.
8.3. Гарантия не распространяется на случаи неправильной эксплуатации, механических повреждений, попадания жидкости, несанкционированного ремонта и нарушения инструкций производителя.
8.4. Для обращения по гарантии Покупатель предоставляет товар, чек и гарантийный талон (при наличии).

# 9. Возврат и обмен
9.1. Товар надлежащего качества Покупатель вправе вернуть или обменять в порядке, установленном законодательством, в течение 10 дней со дня покупки при условии, что товар не был в употреблении, сохранены его товарный вид, упаковка, пломбы, ярлыки и полная комплектация, а также предъявлен чек.
9.2. Товары из перечня, установленного законодательством (в том числе технически сложные бытовые товары с установленным гарантийным сроком), надлежащего качества возврату и обмену не подлежат, если законодательством не предусмотрено иное.
9.3. При обнаружении недостатков Покупатель вправе в соответствии с законодательством потребовать замены товара, безвозмездного ремонта, соразмерного уменьшения цены или возврата денег. При необходимости проводится проверка (экспертиза) товара.
9.4. Деньги за возвращённый товар возвращаются в срок, установленный законодательством, со дня принятия требования, тем же способом, которым была произведена оплата (при оплате наличными — наличными или на банковскую карту, указанную Покупателем).

# 10. Персональные данные
10.1. Оформляя заказ и пользуясь Сайтом, Покупатель в соответствии с Законом «О персональных данных» даёт согласие на обработку своих персональных данных (имя, фамилия, телефон, адрес, email).
10.2. Данные используются только для выполнения заказа, доставки, связи с Покупателем и повышения качества обслуживания. Они передаются только партнёрам, необходимым для выполнения заказа (служба доставки, платёжная система, SMS-сервис).
10.3. Покупатель может в любое время изменить свои данные в Профиле или обратиться к Продавцу с просьбой об их удалении.

# 11. Предотвращение мошенничества
11.1. При выявлении подозрительных заказов (например, использование чужого платёжного средства, множество одинаковых заказов) Продавец вправе дополнительно проверить заказ, попросить Покупателя подтвердить личность или отменить заказ.
11.2. Продавец никогда не запрашивает пароль или SMS-код от своего имени. При получении такого запроса Покупатель не должен сообщать код и должен уведомить Продавца.

# 12. Ответственность сторон и форс-мажор
12.1. Стороны несут ответственность за неисполнение или ненадлежащее исполнение оферты в соответствии с законодательством.
12.2. Стороны не несут ответственности за неисполнение обязательств вследствие обстоятельств непреодолимой силы (стихийные бедствия, война, эпидемии, решения государственных органов, сбои сетей связи и электроснабжения и т. п.).
12.3. Продавец не отвечает за ущерб, причинённый неправильной эксплуатацией товара, и за сбои в работе сервисов третьих лиц (банк, платёжная система, мобильная связь).

# 13. Разрешение споров
13.1. Споры решаются прежде всего путём переговоров. Покупатель может направить претензию по телефону или email; претензия рассматривается в срок, установленный законодательством.
13.2. При недостижении согласия спор разрешается в суде в соответствии с законодательством Республики Узбекистан.

# 14. Реквизиты Продавца
Наименование: [наименование ООО]
ИНН: [ИНН]
Юридический адрес: [адрес]
Банк: [наименование банка], р/с: [расчётный счёт], МФО: [МФО]
Телефон: [телефон]
Email: [email]
Руководитель: [Ф.И.О.]

Редакция от 3 ноября 2026 года"""


def fill_offer(apps, schema_editor):
    StoreSettings = apps.get_model("orders", "StoreSettings")
    store, _ = StoreSettings.objects.get_or_create(pk=1)
    changed = []
    if not store.offer_text.strip():
        store.offer_text = OFFER_UZ
        changed.append("offer_text")
    if not store.offer_text_ru.strip():
        store.offer_text_ru = OFFER_RU
        changed.append("offer_text_ru")
    if changed:
        store.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [("orders", "0010_phone_login")]
    operations = [migrations.RunPython(fill_offer, migrations.RunPython.noop)]
