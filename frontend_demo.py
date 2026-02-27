import streamlit as st
import requests

# 设置页面标题
st.set_page_config(page_title="SE Project Demo", page_icon="🤖")

st.title("🤖 AI Service Prototype")
st.write("This is a frontend demo connected to our FastAPI backend.")

# 定义后端 API 的地址 (注意：Docker 里的地址和本地开发地址可能不同，这里用本地的)
API_URL = "http://127.0.0.1:8000"

# --- 功能 1: 系统健康检查 ---
st.header("1. System Status Check")
if st.button("Check Backend Health"):
    try:
        # 发送请求给后端 /health 接口
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success(f"Backend is Online! Status: {response.json()}")
        else:
            st.error("Backend returned an error.")
    except Exception as e:
        st.error(f"Connection failed: {e}")

# --- 功能 2: AI 功能模拟 ---
st.header("2. AI Feature Demo")
st.info("Enter text below to send it to the backend AI model.")

user_input = st.text_input("Input Text:", "Hello AI")

if st.button("Run AI Prediction"):
    if user_input:
        with st.spinner("Processing..."):
            try:
                # 发送请求给后端 /predict 接口
                response = requests.get(f"{API_URL}/predict", params={"input_text": user_input})
                if response.status_code == 200:
                    result = response.json()
                    st.json(result) #以此展示返回的 JSON 数据
                    st.balloons()   # 放个气球庆祝一下
                else:
                    st.error("Error processing request.")
            except Exception as e:
                st.error(f"Connection error: {e}")
    else:
        st.warning("Please enter some text.")