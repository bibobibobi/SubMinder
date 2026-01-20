from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 1. 初始化 Flask app
app = Flask(__name__)

# 2. 設定 SQLite 資料庫
# 資料庫檔案會建立在專案根目錄，名稱為 subscriptions.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 關閉追蹤修改以節省資源

# 初始化 SQLAlchemy
db = SQLAlchemy(app)

# 3. 建立 Subscription Model
class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # 訂閱名稱 (如 Netflix, Spotify)
    price = db.Column(db.Float, nullable=False)      # 價格
    billing_cycle = db.Column(db.String(50), nullable=False) # 週期 (如 Monthly, Yearly)
    # next_payment_date 存儲日期類型
    next_payment_date = db.Column(db.Date, nullable=False)
    
    # 建立時間 (選用，方便紀錄)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription {self.name}>'

# 4. 啟動時自動建立資料庫表格
# 使用 app_context 確保在 Flask 應用程式環境下執行資料庫操作
with app.app_context():
    db.create_all()
    print("資料庫表格已檢查或建立完成。")

@app.route('/')
def index():
    # 從資料庫撈出所有訂閱資料
    subscriptions = Subscription.query.all()
    # 將資料傳遞給 index.html
    return render_template('index.html', subscriptions=subscriptions)

@app.route('/add', methods=['GET', 'POST'])
def add_subscription():
    if request.method == 'POST':
        # 接收表單資料
        name = request.form.get('name')
        price = request.form.get('price')
        billing_cycle = request.form.get('billing_cycle')
        date_str = request.form.get('next_payment_date')

        # 資料處理：把日期字串 (YYYY-MM-DD) 轉成 Python date 物件
        # 如果使用者沒填日期，這裡會報錯，實際專案通常會加錯誤處理
        payment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # 建立新物件
        new_sub = Subscription(
            name=name,
            price=float(price),
            billing_cycle=billing_cycle,
            next_payment_date=payment_date
        )

        # 寫入資料庫
        db.session.add(new_sub)
        db.session.commit()

        # 完成後導回首頁
        return redirect(url_for('index'))

    # 如果是 GET 請求，就顯示表單
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)