from fastapi import FastAPI, HTTPException, Query
import requests
import os
import uvicorn
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

app = FastAPI(
    title="CryptoPanic News API",
    description="API برای دریافت اخبار و اطلاعات بازار کریپتو از سرویس CryptoPanic",
    version="1.0.0"
)

# دریافت توکن API از متغیرهای محیطی
CRYPTOPANIC_API_TOKEN = os.getenv("CRYPTOPANIC_API_TOKEN")
if not CRYPTOPANIC_API_TOKEN:
    print("⚠️ هشدار: CRYPTOPANIC_API_TOKEN تنظیم نشده است! API به درستی کار نخواهد کرد.")

BASE_URL = "https://cryptopanic.com/api/v1"

@app.get("/")
def home():
    return {"message": "✅ API اخبار CryptoPanic در حال اجراست!", "version": "1.0.0"}

# تابع کمکی برای ارسال درخواست به CryptoPanic
async def fetch_from_cryptopanic(endpoint: str, params: Optional[Dict[str, Any]] = None):
    url = f"{BASE_URL}{endpoint}"
    
    # اضافه کردن توکن احراز هویت به پارامترها
    if params is None:
        params = {}
    
    params["auth_token"] = CRYPTOPANIC_API_TOKEN
    
    print(f"🔍 ارسال درخواست به: {url}")
    print(f"🔍 با پارامترهای: {params}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"✅ وضعیت پاسخ: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ درخواست نامعتبر: {response.text}")
            raise HTTPException(status_code=400, detail=f"❌ درخواست نامعتبر: {response.text}")
        elif response.status_code == 401:
            print(f"❌ خطای احراز هویت: {response.text}")
            raise HTTPException(status_code=401, detail="❌ توکن API نامعتبر است")
        elif response.status_code == 429:
            print(f"❌ تعداد درخواست‌ها بیش از حد مجاز: {response.text}")
            raise HTTPException(status_code=429, detail="❌ تعداد درخواست‌ها بیش از حد مجاز است. لطفاً کمی صبر کنید.")
        else:
            print(f"⚠ خطای غیرمنتظره: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"⚠ خطای غیرمنتظره: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"❌ خطای ارتباط: {str(e)}")
        raise HTTPException(status_code=500, detail=f"❌ خطای ارتباط: {str(e)}")

# 1️⃣ دریافت پست‌های اخیر
@app.get("/news")
async def get_news(
    currencies: Optional[str] = Query(None, description="فیلتر بر اساس ارزها (مثال: BTC,ETH)"),
    filter: Optional[str] = Query(None, description="فیلتر نوع اخبار (rising, hot, bullish, bearish, important, saved, lol)"),
    regions: Optional[str] = Query("en", description="فیلتر بر اساس منطقه زبانی (مثال: en,de,jp)"),
    kind: Optional[str] = Query(None, description="نوع محتوا (news, media)"),
    public: bool = Query(True, description="استفاده از API عمومی"),
    metadata: bool = Query(False, description="دریافت متادیتای اضافی (فقط برای کاربران PRO)"),
    limit: int = Query(50, description="تعداد نتایج (حداکثر 100)")
):
    """
    دریافت اخبار و پست‌های اخیر از CryptoPanic
    """
    params = {}
    
    if currencies:
        params["currencies"] = currencies
    
    if filter:
        params["filter"] = filter
    
    if regions:
        params["regions"] = regions
    
    if kind:
        params["kind"] = kind
    
    if public:
        params["public"] = "true"
    
    if metadata:
        params["metadata"] = "true"
    
    params["limit"] = min(limit, 100)  # محدود کردن به حداکثر 100
    
    return await fetch_from_cryptopanic("/posts/", params)

# 2️⃣ دریافت اخبار برای ارزهای دنبال‌شده
@app.get("/news/following")
async def get_following_news(
    filter: Optional[str] = Query(None, description="فیلتر نوع اخبار (rising, hot, bullish, bearish, important, saved, lol)"),
    regions: Optional[str] = Query("en", description="فیلتر بر اساس منطقه زبانی (مثال: en,de,jp)"),
    kind: Optional[str] = Query(None, description="نوع محتوا (news, media)"),
    metadata: bool = Query(False, description="دریافت متادیتای اضافی (فقط برای کاربران PRO)"),
    limit: int = Query(50, description="تعداد نتایج (حداکثر 100)")
):
    """
    دریافت اخبار مربوط به ارزهای دنبال‌شده (فقط برای استفاده خصوصی)
    """
    params = {"following": "true"}
    
    if filter:
        params["filter"] = filter
    
    if regions:
        params["regions"] = regions
    
    if kind:
        params["kind"] = kind
    
    if metadata:
        params["metadata"] = "true"
    
    params["limit"] = min(limit, 100)  # محدود کردن به حداکثر 100
    
    return await fetch_from_cryptopanic("/posts/", params)

# 3️⃣ دریافت اطلاعات پورتفولیو
@app.get("/portfolio")
async def get_portfolio():
    """
    دریافت اطلاعات پورتفولیو (فقط برای استفاده خصوصی)
    """
    return await fetch_from_cryptopanic("/portfolio/")

# 4️⃣ تست توکن API
@app.get("/test-api-key")
async def test_api_key():
    """
    تست اعتبار توکن API
    """
    try:
        # درخواست اخبار با محدودیت 1 برای تست توکن
        result = await fetch_from_cryptopanic("/posts/", {"limit": 1})
        return {
            "status": "success", 
            "message": "✅ توکن API معتبر است و ارتباط با CryptoPanic برقرار است",
            "post_count": len(result.get("results", []))
        }
    except Exception as e:
        return {"status": "error", "message": f"❌ خطای ارتباط: {str(e)}"}

# اجرای سرور
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8084))  # استفاده از پورت 8084 برای جلوگیری از تداخل با API های دیگر
    print(f"🚀 راه‌اندازی سرور API اخبار CryptoPanic روی پورت {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
