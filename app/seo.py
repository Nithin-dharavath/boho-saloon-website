from dataclasses import dataclass

BASE_URL = "https://bohobloomsalon.com"
SITE_NAME = "Boho Bloom Luxury Salon"
DEFAULT_OG_IMAGE = f"{BASE_URL}/static/images/salon-hero.jpg"
DEFAULT_KEYWORDS = (
    "salon, hair salon, unisex salon, Hanamkonda, Warangal, "
    "luxury salon, beauty salon, hair care, nails, makeup"
)


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
            }
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
