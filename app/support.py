from __future__ import annotations

from typing import Dict, Any, List


class SupportService:
    """Multi-language support & help.

    Designed to be **future-proof**: languages live in a dict keyed by locale
    code. To add a new language later, just add another entry to ``support.lang_config``
    and (optionally) to ``translations``. The Help UI in the mini-app reads
    ``available_languages()`` automatically, so no other code changes are needed.
    """

    # Ordered list of supported locales shown in the Help / language switcher UI.
    # First two are the default populated translations; the rest are added below.
    LANG_ORDER: List[str] = [
        "en", "hi", "mr", "gu", "pa", "bn", "ur", "ta", "te", "ne",
        "ar", "de", "fr", "es", "pt", "it", "ru", "zh", "ja", "ko",
    ]

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
                    "nav_home": "Home", "nav_ads": "Ads", "nav_tasks": "Tasks", "nav_invite": "Invite", "nav_wallet": "Wallet",
                    "spin_title": "🎡 Daily Spin",
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
                    "nav_home": "होम", "nav_ads": "विज्ञापन", "nav_tasks": "कार्य", "nav_invite": "आमंत्रित करें", "nav_wallet": "वॉलेट",
                    "spin_title": "🎡 दैनिक स्पिन",
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
            # Adding famous foreign languages
            "es": { "faq": {"how_to_earn": "Gana monedas completando tareas, viendo anuncios e invitando a amigos."}, "messages": {"help_intro": "Ayuda: completa tareas, mira anuncios, invita a amigos.", "customer_support_button": "Soporte al Cliente", "contact_admin_button": "Contactar al Admin"} },
            "fr": { "faq": {"how_to_earn": "Gagnez des pièces en accomplissant des tâches, en regardant des publicités et en invitant des amis."}, "messages": {"help_intro": "Aide : accomplissez des tâches, regardez des publicités, invitez des amis.", "customer_support_button": "Support Client", "contact_admin_button": "Contacter l'Admin"} },
            "zh": { "faq": {"how_to_earn": "通过完成任务、观看广告和邀请朋友来赚取金币。"}, "messages": {"help_intro": "帮助：完成任务、观看广告、邀请朋友。", "customer_support_button": "客户支持", "contact_admin_button": "联系管理员"} },
            "ru": { "faq": {"how_to_earn": "Зарабатывайте монеты, выполняя задания, просматривая рекламу и приглашая друзей."}, "messages": {"help_intro": "Помощь: выполняйте задания, смотрите рекламу, приглашайте друзей.", "customer_support_button": "Служба поддержки", "contact_admin_button": "Связаться с администратором"} },
            # More languages like 'bn', 'ta', 'te' can be added here.
        }
        self.default_lang = "en"

        # This can also be moved into the translations dict if needed.
        self.moderation_blocklist = {
            "chut", "lund", "bhosdi", "randi", "fuck", "sex", "sexy", "rude",
        }
        
        # This should be configurable via admin panel.
        # Multiple support groups so the user can be routed to any of them.
        self.support_links = {
            "support_group": "https://t.me/+QserNlqLSqZjN2U9",       # Customer Support
            "support_group2": "https://t.me/+CoC4gg7phiA2ZjI1",      # Support (alt)
            "admin_channel": "https://t.me/+nvkRuwvZJnRiOGM1",       # xio_liis Admin Support
            "bot_username": "https://t.me/xiolis_bot",               # Bot username
        }

        # Human-readable locale metadata (flags + labels) for the UI language switcher.
        # Future-proof: add more entries here + in translations to expose new languages.
        self.lang_config: Dict[str, Dict[str, str]] = {
            "en": {"flag": "🇬🇧", "label": "English"},
            "hi": {"flag": "🇮🇳", "label": "हिन्दी"},
            "mr": {"flag": "🇮🇳", "label": "मराठी"},
            "gu": {"flag": "🇮🇳", "label": "ગુજરાતી"},
            "pa": {"flag": "🇮🇳", "label": "ਪੰਜਾਬੀ"},
            "bn": {"flag": "🇧🇩", "label": "বাংলা"},
            "ur": {"flag": "🇵🇰", "label": "اردو"},
            "ta": {"flag": "🇮🇳", "label": "தமிழ்"},
            "te": {"flag": "🇮🇳", "label": "తెలుగు"},
            "ne": {"flag": "🇳🇵", "label": "नेपाली"},
            "ar": {"flag": "🇸🇦", "label": "العربية"},
            "de": {"flag": "🇩🇪", "label": "Deutsch"},
            "fr": {"flag": "🇫🇷", "label": "Français"},
            "es": {"flag": "🇪🇸", "label": "Español"},
            "pt": {"flag": "🇵🇹", "label": "Português"},
            "it": {"flag": "🇮🇹", "label": "Italiano"},
            "ru": {"flag": "🇷🇺", "label": "Русский"},
            "zh": {"flag": "🇨🇳", "label": "中文"},
            "ja": {"flag": "🇯🇵", "label": "日本語"},
            "ko": {"flag": "🇰🇷", "label": "한국어"},
        }

        # Add the remaining languages (beyond the full en/hi, and partial ones)
        # in a maintainable, future-proof way. Each entry includes faq + messages so
        # the support/help feature fully works in that language.
        self._install_extra_languages()

    def _install_extra_languages(self) -> None:
        """Installs the extended language packs.

        Each pack provides localised FAQ + help messages (and optionally UI keys).
        This keeps the translations dict open and easy to extend later.
        """
        self.translations.update({
            "mr": {
                "faq": {
                    "how_to_earn": "सिक्के मिळवण्यासाठी टास्क पूर्ण करा, जाहिराती पहा आणि मित्रांना आमंत्रित करा।",
                    "how_to_withdraw": "पैसे काढण्याचे नियम (आमंत्रण, टास्क, जाहिराती) पूर्ण करा.",
                    "support_group": "अपडेटसाठी सपोर्ट ग्रुपमध्ये सामील व्हा.",
                },
                "messages": {
                    "help_intro": "मदत: टास्क करा, जाहिराती पहा, मित्रांना आमंत्रित करा.",
                    "respectful_chat": "कृपया चॅटमध्ये आदराने बोला.",
                    "support_message_received": "तुमचा संदेश प्राप्त झाला आहे.",
                    "customer_support_button": "💬 ग्राहक सहाय्य",
                    "contact_admin_button": "👑 ऍडमिनशी संपर्क करा",
                },
                "ui": {
                    "coins": "सिक्के", "invites": "आमंत्रणे", "tasks_done": "झालेली कामे",
                    "nav_home": "होम", "nav_ads": "जाहिराती", "nav_tasks": "कार्य",
                    "nav_invite": "आमंत्रित करा", "nav_wallet": "पैसे काढा",
                    "task_complete_button": "पूर्ण करा", "task_completed_badge": "पूर्ण झाले",
                    "withdraw_button": "पैसे काढण्याची विनंती", "no_history": "अद्याप पैसे काढण्याचा इतिहास नाही.",
                },
            },
            "gu": {
                "faq": {
                    "how_to_earn": "સિક્કા મેળવવા કાર્યો પૂર્ણ કરો, જાહેરાતો જુઓ અને મિત્રોને આમંત્રિત કરો.",
                    "how_to_withdraw": "કાઢવાના નિયમો (આમંત્રણ, કાર્યો, જાહેરાતો) પૂર્ણ કરો.",
                    "support_group": "અપડેટ માટે સપોર્ટ ગ્રુપમાં જોડાઓ.",
                },
                "messages": {
                    "help_intro": "મદદ: કાર્યો કરો, જાહેરાતો જુઓ, મિત્રોને આમંત્રિત કરો.",
                    "respectful_chat": "કૃપા કરી ચેટમાં આદર રાખો.",
                    "support_message_received": "તમારો સંદેશ પ્રાપ્ત થયો છે.",
                    "customer_support_button": "💬 ગ્રાહક સહાય",
                    "contact_admin_button": "👑 એડમિનનો સંપર્ક કરો",
                },
                "ui": {
                    "coins": "સિક્કા", "invites": "આમંત્રણો", "tasks_done": "પૂર્ણ કાર્યો",
                    "nav_home": "હોમ", "nav_ads": "જાહેરાતો", "nav_tasks": "કાર્યો",
                    "nav_invite": "આમંત્રિત કરો", "nav_wallet": "કાઢો",
                    "task_complete_button": "પૂર્ણ કરો", "task_completed_badge": "પૂર્ણ થયું",
                    "withdraw_button": "કાઢવાની વિનંતી", "no_history": "હજુ કોઈ ઈતિહાસ નથી.",
                },
            },
            "pa": {
                "faq": {
                    "how_to_earn": "ਸਿੱਕੇ ਕਮਾਉਣ ਲਈ ਕੰਮ ਪੂਰੇ ਕਰੋ, ਵਿਗਿਆਪਨ ਦੇਖੋ ਅਤੇ ਦੋਸਤਾਂ ਨੂੰ ਬੁਲਾਓ।",
                    "how_to_withdraw": "ਕਢਵਾਉਣ ਦੇ ਨਿਯਮ (ਸੱਦੇ, ਕੰਮ, ਵਿਗਿਆਪਨ) ਪੂਰੇ ਕਰੋ।",
                    "support_group": "ਅੱਪਡੇਟ ਲਈ ਸਹਾਇਤਾ ਗਰੁੱਪ ਵਿੱਚ ਸ਼ਾਮਲ ਹੋਵੋ।",
                },
                "messages": {
                    "help_intro": "ਮਦਦ: ਕੰਮ ਕਰੋ, ਵਿਗਿਆਪਨ ਦੇਖੋ, ਦੋਸਤਾਂ ਨੂੰ ਬੁਲਾਓ।",
                    "respectful_chat": "ਕਿਰਪਾ ਕਰਕੇ ਚੈਟ ਵਿੱਚ ਸਤਿਕਾਰ ਬਣਾਈ ਰੱਖੋ।",
                    "support_message_received": "ਤੁਹਾਡਾ ਸੁਨੇਹਾ ਪ੍ਰਾਪਤ ਹੋ ਗਿਆ ਹੈ।",
                    "customer_support_button": "💬 ਗਾਹਕ ਸਹਾਇਤਾ",
                    "contact_admin_button": "👑 ਐਡਮਿਨ ਨਾਲ ਸੰਪਰਕ ਕਰੋ",
                },
                "ui": {
                    "coins": "ਸਿੱਕੇ", "invites": "ਸੱਦੇ", "tasks_done": "ਪੂਰੇ ਕੰਮ",
                    "nav_home": "ਹੋਮ", "nav_ads": "ਵਿਗਿਆਪਨ", "nav_tasks": "ਕੰਮ",
                    "nav_invite": "ਸੱਦਾ", "nav_wallet": "ਕਢਵਾਓ",
                    "task_complete_button": "ਪੂਰਾ ਕਰੋ", "task_completed_badge": "ਪੂਰਾ ਹੋਇਆ",
                    "withdraw_button": "ਕਢਵਾਉਣ ਦੀ ਬੇਨਤੀ", "no_history": "ਹਾਲੇ ਕੋਈ ਇਤਿਹਾਸ ਨਹੀਂ।",
                },
            },
            "ne": {
                "faq": {
                    "how_to_earn": "सिक्का कमाउन कार्यहरू पूरा गर्नुहोस्, विज्ञापन हेर्नुहोस् र साथीहरूलाई बोलाउनुहोस्।",
                    "how_to_withdraw": "निकासी नियमहरू (साथी, कार्य, विज्ञापन) पूरा गर्नुहोस्।",
                    "support_group": "अपडेटका लागि समर्थन समूहमा जोडिनुहोस्।",
                },
                "messages": {
                    "help_intro": "सहायता: कार्य गर्नुहोस्, विज्ञापन हेर्नुहोस्, साथीहरूलाई बोलाउनुहोस्।",
                    "respectful_chat": "कृपया च्याटमा सम्मानजनक व्यवहार गर्नुहोस्।",
                    "support_message_received": "तपाईंको सन्देश प्राप्त भयो।",
                    "customer_support_button": "💬 ग्राहक सहायता",
                    "contact_admin_button": "👑 एडमिनसँग सम्पर्क गर्नुहोस्",
                },
                "ui": {
                    "coins": "सिक्का", "invites": "साथीहरू", "tasks_done": "पूरा कार्यहरू",
                    "nav_home": "गृह", "nav_ads": "विज्ञापन", "nav_tasks": "कार्य",
                    "nav_invite": "बोलाउनुहोस्", "nav_wallet": "निकासी",
                    "task_complete_button": "पूरा गर्नुहोस्", "task_completed_badge": "पूरा भयो",
                    "withdraw_button": "निकासी अनुरोध", "no_history": "अहिलेसम्म इतिहास छैन।",
                },
            },
            "ar": {
                "faq": {
                    "how_to_earn": "أكمل المهام وشاهد الإعلانات وادعُ أصدقاءك لكسب العملات.",
                    "how_to_withdraw": "استوفِ شروط السحب (الدعوات، المهام، الإعلانات).",
                    "support_group": "انضم إلى مجموعة الدعم للتحديثات والمساعدة.",
                },
                "messages": {
                    "help_intro": "المساعدة: أكمل المهام، شاهد الإعلانات، ادعُ الأصدقاء.",
                    "respectful_chat": "يرجى الحفاظ على الاحترام في الدردشة.",
                    "support_message_received": "تم استلام رسالتك.",
                    "customer_support_button": "💬 دعم العملاء",
                    "contact_admin_button": "👑 اتصل بالإدارة",
                },
                "ui": {
                    "coins": "عملات", "invites": "دعوات", "tasks_done": "مهام مكتملة",
                    "nav_home": "الرئيسية", "nav_ads": "إعلانات", "nav_tasks": "مهام",
                    "nav_invite": "دعوة", "nav_wallet": "سحب",
                    "task_complete_button": "إكمال", "task_completed_badge": "مكتمل",
                    "withdraw_button": "طلب السحب", "no_history": "لا يوجد سجل بعد.",
                },
            },
            "de": {
                "faq": {
                    "how_to_earn": "Schließe Aufgaben ab, sieh dir Anzeigen an und lade Freunde ein, um Münzen zu verdienen.",
                    "how_to_withdraw": "Erfülle die Auszahlungsregeln (Einladungen, Aufgaben, Anzeigen).",
                    "support_group": "Tritt der Support-Gruppe für Updates und Hilfe bei.",
                },
                "messages": {
                    "help_intro": "Hilfe: Aufgaben erledigen, Anzeigen ansehen, Freunde einladen.",
                    "respectful_chat": "Bitte bleib im Chat respektvoll.",
                    "support_message_received": "Ihre Nachricht wurde empfangen.",
                    "customer_support_button": "💬 Kundensupport",
                    "contact_admin_button": "👑 Admin kontaktieren",
                },
                "ui": {
                    "coins": "Münzen", "invites": "Einladungen", "tasks_done": "Aufgaben",
                    "nav_home": "Start", "nav_ads": "Anzeigen", "nav_tasks": "Aufgaben",
                    "nav_invite": "Einladen", "nav_wallet": "Auszahlen",
                    "task_complete_button": "Erledigt", "task_completed_badge": "Abgeschlossen",
                    "withdraw_button": "Auszahlung anfordern", "no_history": "Noch keine Historie.",
                },
            },
            "pt": {
                "faq": {
                    "how_to_earn": "Complete tarefas, assista anúncios e convide amigos para ganhar moedas.",
                    "how_to_withdraw": "Cumpra os requisitos de saque (convites, tarefas, anúncios).",
                    "support_group": "Entre no grupo de suporte para atualizações e ajuda.",
                },
                "messages": {
                    "help_intro": "Ajuda: complete tarefas, assista anúncios, convide amigos.",
                    "respectful_chat": "Por favor, mantenha o respeito no chat.",
                    "support_message_received": "Sua mensagem foi recebida.",
                    "customer_support_button": "💬 Suporte ao Cliente",
                    "contact_admin_button": "👑 Contatar Admin",
                },
                "ui": {
                    "coins": "Moedas", "invites": "Convites", "tasks_done": "Tarefas",
                    "nav_home": "Início", "nav_ads": "Anúncios", "nav_tasks": "Tarefas",
                    "nav_invite": "Convidar", "nav_wallet": "Sacar",
                    "task_complete_button": "Concluir", "task_completed_badge": "Concluído",
                    "withdraw_button": "Solicitar saque", "no_history": "Sem histórico ainda.",
                },
            },
            "it": {
                "faq": {
                    "how_to_earn": "Completa le attività, guarda gli annunci e invita gli amici per guadagnare monete.",
                    "how_to_withdraw": "Soddisfa i requisiti di prelievo (inviti, attività, annunci).",
                    "support_group": "Unisciti al gruppo di supporto per aggiornamenti e aiuto.",
                },
                "messages": {
                    "help_intro": "Aiuto: completa attività, guarda annunci, invita amici.",
                    "respectful_chat": "Mantieni il rispetto in chat.",
                    "support_message_received": "Il tuo messaggio è stato ricevuto.",
                    "customer_support_button": "💬 Supporto Clienti",
                    "contact_admin_button": "👑 Contatta Admin",
                },
                "ui": {
                    "coins": "Monete", "invites": "Inviti", "tasks_done": "Attività",
                    "nav_home": "Home", "nav_ads": "Annunci", "nav_tasks": "Attività",
                    "nav_invite": "Invita", "nav_wallet": "Prelievo",
                    "task_complete_button": "Completa", "task_completed_badge": "Completato",
                    "withdraw_button": "Richiedi prelievo", "no_history": "Nessuna cronologia.",
                },
            },
            "ja": {
                "faq": {
                    "how_to_earn": "タスクを完了し、広告を視聴し、友達を招待してコインを獲得しましょう。",
                    "how_to_withdraw": "引き出し要件（招待、タスク、広告）を満たしてください。",
                    "support_group": "サポートグループに参加してください。",
                },
                "messages": {
                    "help_intro": "ヘルプ: タスクを完了し、広告を見て、友達を招待。",
                    "respectful_chat": "チャットでは敬意を払ってください。",
                    "support_message_received": "メッセージを受信しました。",
                    "customer_support_button": "💬 カスタマーサポート",
                    "contact_admin_button": "👑 管理者に連絡",
                },
                "ui": {
                    "coins": "コイン", "invites": "招待", "tasks_done": "完了タスク",
                    "nav_home": "ホーム", "nav_ads": "広告", "nav_tasks": "タスク",
                    "nav_invite": "招待", "nav_wallet": "引き出し",
                    "task_complete_button": "完了", "task_completed_badge": "完了済み",
                    "withdraw_button": "引き出しを依頼", "no_history": "履歴はまだありません。",
                },
            },
            "ko": {
                "faq": {
                    "how_to_earn": "작업을 완료하고, 광고를 시청하고, 친구를 초대하여 코인을 획득하세요.",
                    "how_to_withdraw": "출금 요건(초대, 작업, 광고)을 충족하세요.",
                    "support_group": "업데이트와 도움을 위해 지원 그룹에 가입하세요.",
                },
                "messages": {
                    "help_intro": "도움말: 작업 완료, 광고 시청, 친구 초대.",
                    "respectful_chat": "채팅에서 예의를 지켜주세요.",
                    "support_message_received": "메시지를 수신했습니다.",
                    "customer_support_button": "💬 고객 지원",
                    "contact_admin_button": "👑 관리자에게 연락",
                },
                "ui": {
                    "coins": "코인", "invites": "초대", "tasks_done": "완료 작업",
                    "nav_home": "홈", "nav_ads": "광고", "nav_tasks": "작업",
                    "nav_invite": "초대", "nav_wallet": "출금",
                    "task_complete_button": "완료", "task_completed_badge": "완료됨",
                    "withdraw_button": "출금 요청", "no_history": "아직 기록이 없습니다.",
                },
            },
        })

    def available_languages(self) -> List[str]:
        """Returns the ordered list of supported language codes (for the UI switcher)."""
        return list(self.LANG_ORDER)

    def get_faq(self, lang: str = "en") -> Dict[str, str]:
        pack = self.translations.get(lang) or self.translations[self.default_lang]
        return pack.get("faq", {})

    def build_support_message(self, user_message: str, lang: str = "en") -> Dict[str, object]:
        lang_pack = self.translations.get(lang) or self.translations[self.default_lang]
        normalized = (user_message or "").lower()
        for word in self.moderation_blocklist:
            if word in normalized:
                return {"status": "blocked", "message": lang_pack.get("messages", {}).get("respectful_chat", "")}
        return {"status": "sent", "message": lang_pack.get("messages", {}).get("support_message_received", "")}

    def get_support_links(self) -> Dict[str, str]:
        return self.support_links
