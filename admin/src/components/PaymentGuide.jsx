import { Alert, Collapse, Drawer, Steps, Tag, Typography } from 'antd'
import { CheckCircleFilled, WarningFilled } from '@ant-design/icons'
import ProviderContacts from './ProviderContacts'

const { Paragraph, Text, Title } = Typography

// To'lov sozlamalari bo'yicha to'liq qo'llanma (admin xodimlari uchun)
export default function PaymentGuide({ open, onClose, methods = [] }) {
  return (
    <Drawer open={open} onClose={onClose} size={600} title="To'lov sozlamalari bo'yicha qo'llanma">
      <Paragraph>
        <b>To'lov usuli</b> — mijoz buyurtma berayotganda tanlaydigan to'lash yo'li. Saytda faqat shu yerda
        <b> yoqilgan</b> usullar ko'rinadi. O'chirilgan usul bilan buyurtma berib bo'lmaydi.
      </Paragraph>

      <Title level={5}>Usullar turlari</Title>
      <ul className="guide-list">
        <li>
          <b>Naqd pul</b> va <b>Karta orqali (kuryerga)</b> — kalit talab qilmaydi, darhol yoqish mumkin.
          Pul buyurtma topshirilganda olinadi.
        </li>
        <li>
          <b>Click, Payme, Paynet, Uzum Bank</b> — onlayn to'lov. Har biri bilan alohida shartnoma tuziladi,
          ular ulanish kalitlarini beradi.
        </li>
        <li>
          <b>Muddatli to'lov (nasiya)</b> — hamkor nasiya xizmati orqali bo'lib to'lash. Yoqilsa, saytda
          mahsulotlar yonida "× N oy" narxi ko'rinadi; o'chirilsa — yashiriladi.
        </li>
      </ul>

      <Title level={5}>Onlayn usulni ulash: qadamma-qadam</Title>
      <Steps
        orientation="vertical" size="small"
        items={[
          { status: 'process', title: 'Shartnoma tuzing', content: "To'lov tizimi bilan yuridik shaxs yoki YaTT nomidan." },
          { status: 'process', title: 'Kalitlarni oling', content: 'Har bir usulning "Sozlash" oynasida qayerdan olinishi yozilgan.' },
          { status: 'process', title: 'Kalitlarni kiriting', content: '"Sozlash" tugmasini bosing, maydonlarni to\'ldiring va "Saqlash"ni bosing.' },
          { status: 'process', title: "Sinab ko'ring", content: '"Sinov rejimi" yoqiq holatda pul yechilmaydi — test to\'lov qilib tekshiring.' },
          { status: 'process', title: "Sinov rejimini o'chiring", content: 'Hammasi to\'g\'ri ishlasa, "Sinov rejimi"ni o\'chiring.' },
          { status: 'process', title: 'Usulni yoqing', content: 'Kartochkadagi tugmani yoqing — usul darhol saytda paydo bo\'ladi.' },
        ]}
      />

      <Title level={5}>Kimga murojaat qilish</Title>
      <Paragraph>
        <b>Shartnoma va kalitlar</b> uchun — to'lov tizimining o'ziga (quyidagi manzillar).
        Kalitlarni olganingizdan keyin ularni shu yerda o'zingiz kiritasiz.
        <b> Saytga texnik ulash</b> (to'lov sahifasiga o'tkazish, to'lov natijasini qabul qilish) bo'yicha savollar uchun —
        saytni ishlab chiqqan dasturchiga murojaat qiling.
      </Paragraph>
      <Collapse
        size="small" style={{ marginBottom: 16 }}
        items={methods.filter(m => m.contacts?.links?.length).map(m => ({
          key: m.code, label: m.title, children: <ProviderContacts contacts={m.contacts} compact />,
        }))}
      />
      <Paragraph type="secondary" style={{ fontSize: 12 }}>
        Manzil va telefonlar rasmiy saytlardan 2026-yil noyabrda olingan. O'zgargan bo'lishi mumkin — shubha bo'lsa, rasmiy saytdan tekshiring.
      </Paragraph>

      <Title level={5}>Kartochkadagi belgilar</Title>
      <ul className="guide-list">
        <li><Tag color="blue">tugma yoqiq</Tag> — usul saytda ko'rinadi va ishlaydi.</li>
        <li><Text type="success"><CheckCircleFilled /> Sozlangan</Text> — barcha majburiy kalitlar kiritilgan.</li>
        <li><Text type="warning"><WarningFilled /> Sozlanmagan</Text> — kalitlar yetishmaydi, usulni yoqib bo'lmaydi.</li>
        <li><Tag color="orange">sinov rejimi</Tag> — haqiqiy pul olinmaydi, faqat tekshirish uchun.</li>
        <li><Text type="secondary">Kalit talab qilinmaydi</Text> — naqd va kuryerga karta uchun.</li>
      </ul>

      <Title level={5}>Xavfsizlik</Title>
      <ul className="guide-list">
        <li>Maxfiy kalitlar (Secret key, kassa kaliti, parol) saqlangandan keyin hech qayerda ko'rsatilmaydi — saytda ham, bu yerda ham.</li>
        <li>Kalitni o'zgartirmoqchi bo'lmasangiz, maydonni <b>bo'sh qoldiring</b> — eski kalit saqlanib qoladi.</li>
        <li>Kalitlarni messenjer yoki pochta orqali hech kimga yubormang.</li>
        <li>Kalitlarni bilgan xodim ishdan ketsa, to'lov tizimi kabinetida kalitni yangilab, shu yerga qayta kiriting.</li>
      </ul>

      <Alert
        type="warning" showIcon style={{ margin: '16px 0' }}
        title="Hozirgi holat"
        description={
          <>
            Onlayn usullar (Click, Payme, Paynet, Uzum, nasiya) yoqilganda mijoz ularni buyurtmada tanlay oladi,
            lekin <b>to'lovni avtomatik qabul qilish</b> (to'lov sahifasiga o'tkazish va to'lov natijasini olish)
            keyingi bosqichda ulanadi. Shu paytgacha bu usullarni saytda yoqmaslik tavsiya etiladi.
          </>
        }
      />

      <Title level={5}>Ko'p beriladigan savollar</Title>
      <Collapse
        size="small"
        items={[
          {
            key: 1, label: 'Hamma usullarni o\'chirsam nima bo\'ladi?',
            children: 'Mijozlar buyurtma bera olmaydi — saytda "To\'lov usullari mavjud emas" degan xabar chiqadi. Kamida bittasini yoqiq qoldiring.',
          },
          {
            key: 2, label: 'Usulni o\'chirsam, eski buyurtmalar nima bo\'ladi?',
            children: 'O\'zgarmaydi. Buyurtmalarda tanlangan usul nomi saqlanib qoladi, faqat yangi buyurtmalarda u tanlanmaydi.',
          },
          {
            key: 3, label: 'Saytda usul nomi yoki izohini qanday o\'zgartiraman?',
            children: '"Sozlash" oynasidagi "Saytda ko\'rinishi" bo\'limida. Ruscha nomi bo\'sh bo\'lsa, ruscha saytda o\'zbekcha nom ko\'rinadi.',
          },
          {
            key: 4, label: 'Usullar qaysi tartibda ko\'rinadi?',
            children: '"Tartib raqami" bo\'yicha: kichik raqamli usul birinchi chiqadi.',
          },
          {
            key: 5, label: 'Nasiyada oylar sonini qanday o\'zgartiraman?',
            children: 'Muddatli to\'lov → "Sozlash" → "Muddat (oy)". Saytdagi barcha "× N oy" narxlari shu son bilan qayta hisoblanadi.',
          },
          {
            key: 6, label: 'Usulni yoqmoqchi bo\'lsam, xato chiqyapti',
            children: 'Demak majburiy kalitlar kiritilmagan. Xabarda qaysilari yetishmayotgani yoziladi va sozlash oynasi o\'zi ochiladi.',
          },
        ]}
      />
    </Drawer>
  )
}
