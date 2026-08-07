from __future__ import annotations

from typing import Dict, Any


class SupportService:
    def __init__(self) -> None:
        # Phase 5: Multi-language support structure.
        # All user-facing strings are now here and can be configured by the admin.
        self.translations: Dict[str, Dict[str, Any]] = {
            "en": {
                "faq": {
                    "how_to_earn": "Complete tasks, watch ads, and invite friends to earn coins.",
                    "how_to_withdraw": "Meet the withdrawal rules (invites, tasks, ads) and request a payout from your wallet.",
                    "support_group": "Join the support group for updates and help.",
                },
                "messages": {
                    "help_intro": "Help: complete tasks, watch ads, invite friends, and keep your wallet active.",
                    "respectful_chat": "Please keep the chat respectful.",
                    "support_message_received": "Your support message has been received.",
                    "customer_support_button": "💬 Customer Support",
                    "contact_admin_button": "👑 Contact Admin",
                    "welcome": "Welcome {name}! Use /menu to see all options or launch the Mini App.",
                },
                "ui": {
                    "total_balance": "Total Balance",
                    "coins": "Coins",
                    "invites": "Invites",
                    "tasks_done": "Tasks Done",
                    "connecting_feed": "Connecting to live feed...",
                    "tasks_title": "Tasks",
                    "invite_title": "Invite Friends",
                    "invite_link_label": "Your personal invite link:",
                    "share_invite_button": "Share Invite Link",
                    "nav_home": "Home", "nav_tasks": "Tasks", "nav_invite": "Invite", "nav_wallet": "Wallet",
                    "next_tier_prefix": "Next:",
                    "task_reward": "Reward",
                    "task_complete_button": "Complete",
                    "task_completed_badge": "Completed",
                    "withdraw_title": "Withdraw Funds",
                    "requirements_title": "Withdrawal Requirements",
                    "min_balance": "Minimum Balance",
                    "min_invites": "Minimum Invites",
                    "min_tasks": "Minimum Tasks",
                    "min_ads": "Minimum Ads Watched",
                    "your_progress": "Your Progress",
                    "withdraw_form_title": "Request Payout",
                    "amount_placeholder": "Amount (e.g., 10)",
                    "upi_placeholder": "your-upi-id@okhdfcbank",
                    "withdraw_button": "Request Withdrawal",
                    "history_title": "Withdrawal History",
                    "no_history": "No withdrawal history yet.",
                }
            },
            "hi": {
                "faq": {
                    "how_to_earn": "सिक्के कमाने के लिए टास्क पूरे करें, विज्ञापन देखें और दोस्तों को आमंत्रित करें।",
                    "how_to_withdraw": "निकासी के नियमों (आमंत्रण, टास्क, विज्ञापन) को पूरा करें और अपने वॉलेट से भुगतान का अनुरोध करें।",
                    "support_group": "अपडेट और सहायता के लिए सहायता समूह में शामिल हों।",
                },
                "messages": {
                    "help_intro": "सहायता: टास्क पूरे करें, विज्ञापन देखें, दोस्तों को आमंत्रित करें, और अपने वॉलेट को सक्रिय रखें।",
                    "respectful_chat": "कृपया चैट में सम्मानजनक भाषा का प्रयोग करें।",
                    "support_message_received": "आपका सहायता संदेश प्राप्त हो गया है।",
                    "customer_support_button": "💬 ग्राहक सहायता",
                    "contact_admin_button": "👑 एडमिन से संपर्क करें",
                    "welcome": "नमस्ते {name}! सभी विकल्प देखने के लिए /menu का उपयोग करें या मिनी ऐप लॉन्च करें।",
                },
                "ui": {
                    "total_balance": "कुल शेष",
                    "coins": "सिक्के",
                    "invites": "आमंत्रण",
                    "tasks_done": "किए गए कार्य",
                    "connecting_feed": "लाइव फ़ीड से जुड़ रहा है...",
                    "tasks_title": "कार्य",
                    "invite_title": "मित्रों को आमंत्रित करें",
                    "invite_link_label": "आपका व्यक्तिगत आमंत्रण लिंक:",
                    "share_invite_button": "आमंत्रण लिंक साझा करें",
                    "nav_home": "होम", "nav_tasks": "कार्य", "nav_invite": "आमंत्रित करें", "nav_wallet": "वॉलेट",
                    "next_tier_prefix": "अगला:",
                    "task_reward": "इनाम",
                    "task_complete_button": "पूरा करें",
                    "task_completed_badge": "पूरा हुआ",
                    "withdraw_title": "धनराशि निकालें",
                    "requirements_title": "निकासी की शर्तें",
                    "min_balance": "न्यूनतम शेषराशि",
                    "min_invites": "न्यूनतम आमंत्रण",
                    "min_tasks": "न्यूनतम कार्य",
                    "min_ads": "देखे गए न्यूनतम विज्ञापन",
                    "your_progress": "आपकी प्रगति",
                    "withdraw_form_title": "भुगतान का अनुरोध करें",
                    "amount_placeholder": "राशि (उदा. 10)",
                    "upi_placeholder": "your-upi-id@okhdfcbank",
                    "withdraw_button": "निकासी का अनुरोध करें",
                    "history_title": "निकासी का इतिहास",
                    "no_history": "अभी तक कोई निकासी इतिहास नहीं है।",
                }
            },
            # Adding placeholders for other requested languages
            "bn": { "faq": {"how_to_earn": "কাজ সম্পূর্ণ করে, বিজ্ঞাপন দেখে এবং বন্ধুদের আমন্ত্রণ জানিয়ে কয়েন উপার্জন করুন।"}, "messages": {"help_intro": "সাহায্য: কাজ সম্পূর্ণ করুন, বিজ্ঞাপন দেখুন, বন্ধুদের আমন্ত্রণ জানান।", "customer_support_button": "গ্রাহক সহায়তা", "contact_admin_button": "অ্যাডমিনের সাথে যোগাযোগ করুন"} },
            "ur": { "faq": {"how_to_earn": "کام مکمل کرکے، اشتہارات دیکھ کر، اور دوستوں کو مدعو کرکے سکے حاصل کریں۔"}, "messages": {"help_intro": "مدد: کام مکمل کریں، اشتہارات دیکھیں، دوستوں کو مدعو کریں۔", "customer_support_button": "کسٹمر سپورٹ", "contact_admin_button": "ایڈمن سے رابطہ کریں"} },
            "ta": { "faq": {"how_to_earn": "பணிகளை முடிப்பதன் மூலமும், விளம்பரங்களைப் பார்ப்பதன் மூலமும், நண்பர்களை அழைப்பதன் மூலமும் நாணயங்களைப் பெறுங்கள்."}, "messages": {"help_intro": "உதவி: பணிகளை முடிக்கவும், விளம்பரங்களைப் பார்க்கவும், நண்பர்களை அழைக்கவும்.", "customer_support_button": "வாடிக்கையாளர் ஆதரவு", "contact_admin_button": "நிர்வாகியைத் தொடர்புகொள்க"} },
            "te": { "faq": {"how_to_earn": "పనులను పూర్తి చేయడం, ప్రకటనలను చూడటం మరియు స్నేహితులను ఆహ్వానించడం ద్వారా నాణేలను సంపాదించండి."}, "messages": {"help_intro": "సహాయం: పనులను పూర్తి చేయండి, ప్రకటనలను చూడండి, స్నేహితులను ఆహ్వానించండి.", "customer_support_button": "వినియోగదారుల సహాయ కేంద్రం", "contact_admin_button": "నిర్వాహకుడిని సంప్రదించండి"} },
            # More languages like 'bn', 'ta', 'te' can be added here.
        }
        self.default_lang = "en"

        # This can also be moved into the translations dict if needed.
        self.moderation_blocklist = {
            "chut", "lund", "bhosdi", "randi", "fuck", "sex", "sexy", "rude",
        }
        
        # This should be configurable via admin panel.
        self.support_links = {
            "support_group": "https://t.me/+QserNlqLSqZjN2U9", # Customer Support
            "admin_channel": "https://t.me/Earnmoneyxio", # Contact Admin
        }

    def get_faq(self, lang: str = "en") -> Dict[str, str]:
        return self.translations.get(lang, self.translations[self.default_lang])["faq"]

    def build_support_message(self, user_message: str, lang: str = "en") -> Dict[str, object]:
        lang_pack = self.translations.get(lang, self.translations[self.default_lang])
        normalized = (user_message or "").lower()
        for word in self.moderation_blocklist:
            if word in normalized:
                return {"status": "blocked", "message": lang_pack["messages"]["respectful_chat"]}
        return {"status": "sent", "message": lang_pack["messages"]["support_message_received"]}

    def get_support_links(self) -> Dict[str, str]:
        return self.support_links
