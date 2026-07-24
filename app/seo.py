from dataclasses import dataclass

BASE_URL = "https://bohobloomsalon.com"
SITE_NAME = "Boho Bloom Luxury Salon"
DEFAULT_OG_IMAGE = f"{BASE_URL}/static/images/salon-hero.jpg"
DEFAULT_KEYWORDS = (
    "salon, hair salon, unisex salon, Hanamkonda, Warangal, "
    "luxury salon, beauty salon, hair care, nails, makeup"
)

SAME_AS_URLS = [
    "https://www.instagram.com/bohobloomsalon/",
    "https://www.facebook.com/bohobloomsalon/",
]


@dataclass
class SEOMeta:
    title: str
    description: str = ""
    keywords: str = DEFAULT_KEYWORDS
    og_image: str = DEFAULT_OG_IMAGE
    canonical: str = BASE_URL
    robots: str = "index, follow"
    og_type: str = "website"

    def to_context(self) -> dict:
        return {
            "seo": {
                "title": self.title,
                "description": self.description,
                "keywords": self.keywords,
                "og_image": self.og_image,
                "og_url": self.canonical,
                "og_type": self.og_type,
                "canonical": self.canonical,
                "robots": self.robots,
                "site_name": SITE_NAME,
                "base_url": BASE_URL,
            },
            "same_as_urls": SAME_AS_URLS,
        }


INDEX_SEO = SEOMeta(
    title="Boho Bloom Luxury Salon | Hanamkonda, Warangal",
    description=(
        "Boho Bloom Luxury Salon is a premium unisex salon in Hanamkonda, "
        "Warangal, offering hair care, nails, and makeup services. "
        "Open daily 9:00 am to 9:00 pm."
    ),
    canonical=f"{BASE_URL}/",
    keywords=(
        "salon, hair salon, unisex salon, Hanamkonda, Warangal, "
        "luxury salon, beauty salon, hair care, nails, makeup, "
        "premium salon, Telangana salon, bridal makeup, hair styling"
    ),
)

LOGIN_SEO = SEOMeta(
    title="Sign In — Boho Bloom Luxury Salon",
    description=(
        "Sign in to your Boho Bloom Luxury Salon account to manage "
        "appointments and preferences."
    ),
    canonical=f"{BASE_URL}/login",
    robots="noindex, follow",
)

PROFILE_SETUP_SEO = SEOMeta(
    title="Complete Your Profile — Boho Bloom Luxury Salon",
    description=(
        "Complete your Boho Bloom profile to personalise your salon experience."
    ),
    canonical=f"{BASE_URL}/profile/setup",
    robots="noindex, follow",
)

ADMIN_LOGS_SEO = SEOMeta(
    title="Automation Logs — Boho Bloom",
    description="",
    robots="noindex, nofollow",
)

PRIVACY_SEO = SEOMeta(
    title="Privacy Policy — Boho Bloom Luxury Salon",
    description=(
        "Read the privacy policy of Boho Bloom Luxury Salon. Learn how we collect, "
        "use, and protect your personal information."
    ),
    canonical=f"{BASE_URL}/privacy-policy",
    robots="index, follow",
)

TERMS_SEO = SEOMeta(
    title="Terms &amp; Conditions — Boho Bloom Luxury Salon",
    description=(
        "Review the terms and conditions of Boho Bloom Luxury Salon including "
        "appointment policies, pricing, and liability information."
    ),
    canonical=f"{BASE_URL}/terms-conditions",
    robots="index, follow",
)

SERVICES_SEO = SEOMeta(
    title="Services — Boho Bloom Luxury Salon | Hair, Beauty, Nails & Spa",
    description=(
        "Explore premium hair care, beauty, nail art, spa, and bridal services at Boho "
        "Bloom Luxury Salon in Hanamkonda, Warangal. Also available: men's grooming and "
        "combo offers."
    ),
    canonical=f"{BASE_URL}/services",
    keywords=(
        "salon services, hair care, hair color, highlights, balayage, keratin, "
        "bridal makeup, manicure, pedicure, nail art, spa, facial, "
        "men's grooming, beard trim, Hanamkonda, Warangal, salon combo offers"
    ),
)
