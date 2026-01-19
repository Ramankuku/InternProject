import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

PRODUCTS = [
    {
        "id": 1,
        "name": "Smartphone",
        "price": 15000,
        "image_url": "assests/s_phone.jpg"
    },
    {
        "id": 2,
        "name": "Headphones",
        "price": 2000,
        "image_url": "assests/h_headphone.jpg"
    },
    {
        "id": 3,
        "name": "💻 Laptop",
        "price": 58000,
        "image_url": "assests/laptop.jpg"
    },
    {
        "id": 4,
        "name": "Iphone 16",
        "price": 60000,
        "image_url": "assests/laptop.jpg"
    },
]

st.set_page_config(
    page_title="Mini E-Commerce BNPL",
    page_icon="🛒",
    layout="centered"
)


st.markdown("""
<style>
.card {
    padding: 15px;
    border-radius: 12px;
    background-color: #f8f9fa;
    margin-bottom: 10px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}
.price {
    font-weight: bold;
    color: #2c7be5;
}
.risk-low { color: green; font-weight: bold; }
.risk-medium { color: orange; font-weight: bold; }
.risk-high { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛒 Mini E-Commerce BNPL App")
st.caption("Smart shopping with financial risk awareness")

if "cart" not in st.session_state:
    st.session_state.cart = []

menu = st.sidebar.radio("📌 Menu", ["Signup", "Login", "Shop", "Bag", "Logout"])

if menu == "Signup":
    st.subheader("📝 Create Account")

    user_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        res = requests.post(
            f"{API_URL}/signup",
            json={"user_id": user_id, "password": password}
        )
        st.info(res.json()["message"])

elif menu == "Login":
    st.subheader("🔐 Login")

    user_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = requests.post(
            f"{API_URL}/login",
            json={"user_id": user_id, "password": password}
        )
        data = res.json()
        st.info(data["message"])

        if data["status"] == "success":
            st.session_state.user_id = user_id

elif menu == "Shop":
    if "user_id" not in st.session_state:
        st.warning("Please login first")
    else:
        st.subheader("🛍 Available Products")

        for p in PRODUCTS:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(p["image_url"], use_container_width=True)

            with col2:
                st.markdown(f"### {p['name']}")
                st.markdown(f"**₹{p['price']}**")

                if st.button("➕ Add to Bag", key=p["id"]):
                    st.session_state.cart.append(p)
                    st.success("Added to bag")

elif menu == "Bag":
    if "user_id" not in st.session_state:
        st.warning("Please login first")
    else:
        st.subheader("🛒 Your Bag")

        if not st.session_state.cart:
            st.info("Your bag is empty")
        else:
            total = 0

            for item in st.session_state.cart:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(item["image_url"], width=80)
                with col2:
                    st.write(f"{item['name']} — ₹{item['price']}")

                total += item["price"]

            st.divider()
            st.subheader(f"💰 Total Amount: ₹{total}")

            if st.button("💳 Pay Now"):
                res = requests.post(
                    f"{API_URL}/pay/{st.session_state.user_id}"
                )
                data = res.json()

                risk = data["risk_level"]

                if "Low" in risk:
                    st.markdown(
                        f"Risk Level: <span class='risk-low'>{risk}</span>",
                        unsafe_allow_html=True
                    )
                elif "Medium" in risk:
                    st.markdown(
                        f"Risk Level: <span class='risk-medium'>{risk}</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"Risk Level: <span class='risk-high'>{risk}</span>",
                        unsafe_allow_html=True
                    )
                
                if data['status'] == 'declined':
                    st.error('Payment Declined')
                    st.warning(data["explanation"])
                
                else:
                    st.warning(data["explanation"])
                    st.success("Payment Successful ✅")
                
                    st.session_state.cart.clear()

elif menu == "Logout":
    st.session_state.clear()
    st.success("Logged out successfully")
