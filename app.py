from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from dotenv import load_dotenv

app = Flask(__name__)
# --- 資料庫連線設定 (統一使用 PostgreSQL) ---
# 從環境變數抓取 DATABASE_URL
database_url = os.environ.get('DATABASE_URL')

# 確保一定有抓到網址，如果沒抓到 (例如 .env 沒設好) 就報錯提醒
if not database_url:
    raise ValueError("錯誤：找不到 DATABASE_URL，請確認 .env 檔案或 Render 設定已完成！")

# 修正 Render 網址格式 (postgres:// -> postgresql://)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Model 定義 ---
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    billing_cycle = db.Column(db.String(50), nullable=False)
    next_payment_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription {self.name}>'

# 啟動時建立資料庫
with app.app_context():
    db.create_all()

    # 如果資料庫是空的，就自動加幾筆範例資料
    if not Subscription.query.first():
        print("資料庫為空，正在寫入範例資料...")
        
        demo_subs = [
            Subscription(name='Netflix', price=270, billing_cycle='Monthly', next_payment_date=date(2026, 2, 15)),
            Subscription(name='Spotify', price=149, billing_cycle='Monthly', next_payment_date=date(2026, 2, 5)),
            Subscription(name='Adobe CC', price=1680, billing_cycle='Yearly', next_payment_date=date(2026, 12, 20)),
            Subscription(name='Gym', price=999, billing_cycle='Monthly', next_payment_date=date.today()) # 今天扣款，展示警告效果
        ]
        
        for sub in demo_subs:
            db.session.add(sub)
        
        db.session.commit()
        print("範例資料寫入完成！")

# --- 路由 ---

# 1. 首頁：顯示列表 & 計算總金額 & 計算倒數
@app.route('/')
def index():
    subscriptions = Subscription.query.all()
    
    today = date.today()
    total_monthly_cost = 0

    for sub in subscriptions:
        # 計算每月平均花費
        if sub.billing_cycle == 'Monthly':
            total_monthly_cost += sub.price
        elif sub.billing_cycle == 'Yearly':
            total_monthly_cost += sub.price / 12
        elif sub.billing_cycle == 'Weekly':
            total_monthly_cost += sub.price * 4
        
        # 計算倒數天數 (掛載到物件上供 HTML 使用)
        delta = sub.next_payment_date - today
        sub.days_left = delta.days

    # 轉成整數顯示
    total_monthly_cost = int(total_monthly_cost)

    return render_template('index.html', subscriptions=subscriptions, total_cost=total_monthly_cost)


# 2. 新增訂閱
@app.route('/add', methods=['GET', 'POST'])
def add_subscription():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        billing_cycle = request.form.get('billing_cycle')
        date_str = request.form.get('next_payment_date')

        # 錯誤處理
        if not name or not price or not date_str:
            return render_template('add.html', error="錯誤：所有欄位都必須填寫！")
        
        try:
            payment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return render_template('add.html', error="錯誤：日期格式不正確")

        new_sub = Subscription(
            name=name,
            price=float(price),
            billing_cycle=billing_cycle,
            next_payment_date=payment_date
        )

        db.session.add(new_sub)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add.html')


# 3. 編輯訂閱
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_subscription(id):
    sub = Subscription.query.get_or_404(id)

    if request.method == 'POST':
        sub.name = request.form.get('name')
        sub.price = float(request.form.get('price'))
        sub.billing_cycle = request.form.get('billing_cycle')
        
        date_str = request.form.get('next_payment_date')
        sub.next_payment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', sub=sub)


# 4. 刪除訂閱
@app.route('/delete/<int:id>')
def delete_subscription(id):
    subscription_to_delete = Subscription.query.get_or_404(id)
    
    try:
        db.session.delete(subscription_to_delete)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "刪除時發生錯誤"


if __name__ == '__main__':
    app.run(debug=True)