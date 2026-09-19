import logging
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import requests
from django.utils.text import slugify
from blog.models import BlogPost

logger = logging.getLogger(__name__)

MEDIUM_FEED_URL = "https://medium.com/feed/@{username}"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

XML_NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "atom": "http://www.w3.org/2005/Atom",
}


def strip_html(html_str: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    text = re.sub(r"<[^>]+>", " ", html_str)
    return " ".join(text.split())


def extract_cover_image(html_str: str) -> str:
    """
    Extracts the first legitimate image URL from the article content,
    ignoring Medium analytics/tracking pixels.
    """
    images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_str, re.IGNORECASE)
    for img in images:
        if "medium.com/_/stat" in img or "stat?event=" in img:
            continue
        return img
    return ""


def clean_medium_content(html_str: str) -> str:
    """
    Removes Medium tracking pixels and leading duplicate title if present.
    """
    # Remove tracking pixels
    cleaned = re.sub(
        r'<img[^>]+src=["\']https?://medium\.com/_/stat\?[^"\']*["\'][^>]*>',
        "",
        html_str,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def extract_excerpt(html_str: str, max_length: int = 240) -> str:
    """Extracts a short subtitle / excerpt from initial paragraphs."""
    p_matches = re.findall(r"<p>(.*?)</p>", html_str, re.DOTALL | re.IGNORECASE)
    for p in p_matches:
        text = strip_html(p)
        if len(text) > 30:
            if len(text) > max_length:
                return text[:max_length].rsplit(" ", 1)[0] + "…"
            return text
    # Fallback to general plain text
    plain = strip_html(html_str)
    if len(plain) > max_length:
        return plain[:max_length].rsplit(" ", 1)[0] + "…"
    return plain


def calculate_read_time(html_str: str) -> int:
    """Computes estimated read time (assuming ~200 words per minute)."""
    words = len(strip_html(html_str).split())
    return max(1, round(words / 200))


def sync_medium_posts(username: str = "khalfanathman") -> dict:
    """
    Fetches the Medium RSS feed for the given username, parses articles,
    extracts images, tags, read times, and content, and creates or updates
    BlogPost records in the database.
    """
    feed_url = MEDIUM_FEED_URL.format(username=username)
    logger.info("Fetching Medium feed from %s", feed_url)

    try:
        response = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch Medium RSS feed: %s", e)
        return {
            "success": False,
            "error": f"Failed to fetch Medium feed: {str(e)}",
            "created": 0,
            "updated": 0,
            "total_found": 0,
            "articles": [],
        }

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        logger.error("XML parse error on Medium feed: %s", e)
        return {
            "success": False,
            "error": f"Invalid XML from Medium: {str(e)}",
            "created": 0,
            "updated": 0,
            "total_found": 0,
            "articles": [],
        }

    items = root.findall(".//item")
    created_count = 0
    updated_count = 0
    processed_articles = []

    for item in items:
        title = (item.findtext("title") or "").strip()
        if not title:
            continue

        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        pub_date_str = (item.findtext("pubDate") or "").strip()

        pub_date = None
        if pub_date_str:
            try:
                pub_date = parsedate_to_datetime(pub_date_str)
            except Exception:
                pub_date = None

        categories = [
            c.text.strip() for c in item.findall("category") if c.text and c.text.strip()
        ]

        # Extract full HTML content from content:encoded
        enc_elem = item.find("content:encoded", XML_NAMESPACES)
        raw_content = (
            enc_elem.text if enc_elem is not None else item.findtext("description") or ""
        )
        content = clean_medium_content(raw_content)

        cover_image = extract_cover_image(raw_content)
        subtitle = extract_excerpt(raw_content)
        read_time = calculate_read_time(raw_content)

        # Lookup existing post by medium_guid, canonical_url, or exact title
        post = None
        if guid:
            post = BlogPost.objects.filter(medium_guid=guid).first()
        if not post and link:
            post = BlogPost.objects.filter(canonical_url=link).first()
        if not post:
            post = BlogPost.objects.filter(title__iexact=title).first()

        if post:
            # Update existing article
            post.title = title
            post.content = content
            if cover_image:
                post.cover_image = cover_image
            if subtitle and not post.subtitle:
                post.subtitle = subtitle
            post.source = "medium"
            post.canonical_url = link or post.canonical_url
            post.medium_guid = guid or post.medium_guid
            post.tags = list(set(post.tags + categories)) if post.tags else categories
            post.read_time_minutes = read_time
            if pub_date:
                post.published_at = pub_date
            post.is_published = True
            post.save()
            updated_count += 1
            is_new = False
        else:
            # Create new article with a clean slug
            base_slug = slugify(title) or "medium-post"
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            post = BlogPost.objects.create(
                title=title,
                slug=slug,
                subtitle=subtitle,
                content=content,
                cover_image=cover_image,
                source="medium",
                canonical_url=link,
                medium_guid=guid,
                tags=categories,
                read_time_minutes=read_time,
                is_published=True,
                is_featured=False,
                published_at=pub_date,
            )
            created_count += 1
            is_new = True

        processed_articles.append(
            {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "is_new": is_new,
                "cover_image": post.cover_image,
                "read_time_minutes": post.read_time_minutes,
                "canonical_url": post.canonical_url,
            }
        )

    return {
        "success": True,
        "total_found": len(items),
        "created": created_count,
        "updated": updated_count,
        "articles": processed_articles,
    }
