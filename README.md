# Xio_liis PayPlus

A Telegram-based earning bot with an integrated mini web app, designed to help users (students, housewives, children) earn money through various activities. The bot leverages engaging features and a sustainable economic model where the admin doesn't need to invest upfront.

## Features

-   **Dual Wallets:** Separate wallets for bot interactions and mini-app earnings.
-   **Diverse Earning Methods:** Complete tasks, watch ads, claim daily bonuses, spin the wheel, and invite friends.
-   **Secure Withdrawals:** Unique verification codes, admin approval, and specific requirements (invites, tasks, ads) ensure secure payouts.
-   **Admin Panel:** Comprehensive control over bot settings, user profiles, and data management without code changes.
-   **Engaging UI/UX:** Utilizes dark patterns like fake live withdrawal feeds, simulated chat messages, and a tiered progression system to keep users motivated.
-   **Multilingual Support:** Help and FAQs available in multiple languages (English, Hindi, etc.).
-   **Data Management:** Backup and rollback system for data safety.

---

# Xio_liis PayPlus

एक Telegram-आधारित कमाई करने वाला बॉट जिसमें एक एकीकृत मिनी वेब ऐप है, जिसे उपयोगकर्ताओं (छात्रों, गृहिणियों, बच्चों) को विभिन्न गतिविधियों के माध्यम से पैसे कमाने में मदद करने के लिए डिज़ाइन किया गया है। बॉट आकर्षक सुविधाओं और एक स्थायी आर्थिक मॉडल का लाभ उठाता है जहाँ एडमिन को शुरू में निवेश करने की आवश्यकता नहीं होती है।

## विशेषताएँ

-   **दोहरे वॉलेट:** बॉट इंटरैक्शन और मिनी-ऐप कमाई के लिए अलग-अलग वॉलेट।
-   **विविध कमाई के तरीके:** टास्क पूरे करें, विज्ञापन देखें, दैनिक बोनस का दावा करें, स्पिन व्हील खेलें और दोस्तों को आमंत्रित करें।
-   **सुरक्षित निकासी:** अद्वितीय सत्यापन कोड, एडमिन अनुमोदन, और विशिष्ट आवश्यकताएँ (आमंत्रण, टास्क, विज्ञापन) सुरक्षित भुगतान सुनिश्चित करती हैं।
-   **एडमिन पैनल:** कोड में बदलाव किए बिना बॉट सेटिंग्स, उपयोगकर्ता प्रोफाइल और डेटा प्रबंधन पर व्यापक नियंत्रण।
-   **आकर्षक UI/UX:** उपयोगकर्ताओं को प्रेरित रखने के लिए नकली लाइव निकासी फ़ीड, नकली चैट संदेश और एक स्तरीय प्रगति प्रणाली जैसे डार्क पैटर्न का उपयोग करता है।
-   **बहुभाषी समर्थन:** कई भाषाओं (अंग्रेजी, हिंदी, आदि) में सहायता और अक्सर पूछे जाने वाले प्रश्न उपलब्ध हैं।
-   **डेटा प्रबंधन:** डेटा सुरक्षा के लिए बैकअप और रोलबैक सिस्टम।

## Run locally

### 1) Install dependencies

```bash
py -m pip install -r requirements.txt
```

### 2) Run the bot engine

```bash
py main.py
```

### 3) Run the mini app

```bash
py -m flask --app app.mini_app run
```

Then open http://127.0.0.1:5000/ in your browser.

## Ads integration skeleton

The app includes a reusable ads layer in [app/ads.py](app/ads.py) with:

- provider selection (AdMob or AdinPlay)
- reward config
- daily limit and cooldown settings
- widget metadata for future UI integration

You can change the provider via the environment variable `ADS_PROVIDER`.

## Render deployment

This project includes:

- [render.yaml](render.yaml)
- [Procfile](Procfile)

### Deploy steps

1. Create a new Render web service.
2. Connect this repository.
3. Use the default Python environment.
4. Render will install dependencies and start the app using the provided entry point.

### Environment variables

Set these secrets in your Render service environment:

-   `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather.
-   `TELEGRAM_BOT_USERNAME`: Your bot's username (e.g., `xio_liis_bot`).
-   `ADMIN_KEY`: A secret key for accessing the admin panel (e.g., `admin-xio-super-secret`).

The `render.yaml` file will automatically handle other variables like `SECRET_KEY` and `MINI_APP_URL`.

## Future extension points

The project is organized so you can extend it without rewriting the core logic:

- connect a real Telegram bot webhook or polling loop
- add database persistence later without changing the engine API
- add more ads, invite, and task rules in the existing service layer
- replace the current demo HTML with a richer UI while keeping the same routes
- plug in real payment providers, analytics, and admin controls
