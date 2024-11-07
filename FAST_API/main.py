from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal, init_db
from models import User, Product as SQLAlchemyProduct  # Импортируйте SQLAlchemy модель
from schemas import UserCreate, ProductCreate, Product  # Импортируйте Pydantic модели
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt

# Инициализация базы данных
init_db()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для создания токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Корневой маршрут
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Регистрация пользователя
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/", status_code=303)

# Авторизация пользователя
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not pwd_context.verify(password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return RedirectResponse(url="/products", status_code=303)

# Управление продуктами
@app.get("/products", response_class=HTMLResponse)
def products_form(request: Request, db: Session = Depends(get_db)):
    products = db.query(SQLAlchemyProduct).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

@app.post("/products/")
def create_product(name: str = Form(...), description: str = Form(...), price: int = Form(...), db: Session = Depends(get_db)):
    db_product = SQLAlchemyProduct(name=name, description=description, price=price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return RedirectResponse(url="/products", status_code=303)

@app.get("/products/update/{product_id}", response_class=HTMLResponse)
def update_product_form(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(SQLAlchemyProduct).filter(SQLAlchemyProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("product_form.html", {"request": request, "product": product})

@app.post("/products/update/{product_id}")
def update_product(product_id: int, name: str = Form(...), description: str = Form(...), price: int = Form(...), db: Session = Depends(get_db)):
    product = db.query(SQLAlchemyProduct).filter(SQLAlchemyProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = name
    product.description = description
    product.price = price
    db.commit()
    return RedirectResponse(url="/products", status_code=303)

@app.post("/products/delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(SQLAlchemyProduct).filter(SQLAlchemyProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return RedirectResponse(url="/products", status_code=303)
