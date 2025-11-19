import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# --- 1. CẤU HÌNH TRANG & SESSION STATE ---
st.set_page_config(
    page_title="Climate Impact Strategic Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Ẩn sidebar để tập trung vào luồng câu chuyện
)

# Khởi tạo trạng thái trang (Navigation State)
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Overview'

def navigate_to(page):
    st.session_state['current_page'] = page
    st.rerun()

# --- 2. XỬ LÝ DỮ LIỆU (DATA PROCESSING) ---
@st.cache_data
def load_and_process_data():
    try:
        df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')
    except FileNotFoundError:
        st.error("⚠️ Không tìm thấy file dữ liệu. Vui lòng kiểm tra lại.")
        return None

    # Basic Cleaning
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['year'].astype(int)
    
    # --- Feature Engineering cho BQ1 ---
    # 1. Developed Status
    developed_countries = [
        'United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'Italy', 'Canada',
        'Australia', 'South Korea', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium',
        'Austria', 'Denmark', 'Finland', 'Norway', 'Ireland', 'New Zealand', 'Singapore'
    ]
    df['is_developed'] = df['country'].isin(developed_countries)
    df['dev_status'] = df['is_developed'].map({True: 'Developed', False: 'Developing'})

    # 2. Response Bins (Quan trọng cho DQ3.1)
    bins_resp = [0, 6, 24, 72, np.inf]
    labels_resp = ['<6h (Siêu tốc)', '6-24h (Nhanh)', '24-72h (Chậm)', '>72h (Rất chậm)']
    df['response_bin'] = pd.cut(df['response_time_hours'], bins=bins_resp, labels=labels_resp, include_lowest=True)

    # 3. Rates (Deaths/Injuries per capita)
    df['death_rate'] = (df['deaths'] / df['affected_population']) * 100
    df['injury_rate'] = (df['injuries'] / df['affected_population']) * 100

    # 4. Continent Mapping (Cho DQ3.3 - Mapping thủ công các nước lớn để demo)
    def get_continent(country):
        asia = ['China', 'India', 'Japan', 'South Korea', 'Indonesia', 'Philippines', 'Vietnam', 'Thailand', 'Singapore']
        europe = ['Germany', 'United Kingdom', 'France', 'Italy', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium', 'Austria', 'Poland']
        americas = ['United States', 'Canada', 'Brazil', 'Mexico', 'Argentina']
        africa = ['Nigeria', 'Egypt', 'South Africa', 'Kenya', 'Ethiopia']
        if country in asia: return 'Asia'
        if country in europe: return 'Europe'
        if country in americas: return 'Americas'
        if country in africa: return 'Africa'
        return 'Other' # Các nước còn lại
    
    df['continent'] = df['country'].apply(get_continent)

    # --- Feature Engineering cho BQ2 ---
    # 5. Scale Bins (Affected Population)
    bins_pop = [0, 100000, 1000000, 5000000, df['affected_population'].max()+1]
    labels_pop = ['<100k', '100k–1M', '1M–5M', '>5M (Mega-event)']
    df['scale'] = pd.cut(df['affected_population'], bins=bins_pop, labels=labels_pop)

    # 6. Log impact cho EDA
    df['log_impact'] = np.log1p(df['economic_impact_million_usd'])

    return df

df = load_and_process_data()

# --- 3. HÀM VẼ CÁC TRANG (RENDER PAGES) ---

def render_overview():
    st.title("🌍 Global Climate Impact Dashboard")
    st.markdown("### *Phân tích Chiến lược từ Dữ liệu Thực tế (2020-2025)*")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng Sự Kiện", f"{len(df):,}", "Dataset Scope")
    k2.metric("Tổng Thiệt Hại", f"${df['economic_impact_million_usd'].sum():,.0f} M", "Economic Loss")
    k3.metric("Người bị ảnh hưởng", f"{df['affected_population'].sum():,.0f}", "Total Affected")
    k4.metric("Tốc độ Ứng phó TB", f"{df['response_time_hours'].mean():.1f} giờ", "Avg Response Time")
    
    st.markdown("---")
    
    # EDA & Domain Knowledge
    st.subheader("🔍 Tổng Quan & Domain Knowledge (EDA)")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Map Distribution
        fig_map = px.scatter_geo(
            df, lat='latitude', lon='longitude', color='event_type',
            size='log_impact', hover_name='country', projection="natural earth",
            title="Phân bố Địa lý & Tác động (Bong bóng = Log Impact)"
        )
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    with col2:
        st.info("""
        **💡 Domain Knowledge rút ra từ EDA:**
        1. **Dữ liệu lệch (Skewness):** Thiệt hại và số người chết phân phối lệch phải nghiêm trọng (Right-skewed).
           *-> Chiến lược:* Không dùng giá trị trung bình (mean) đơn thuần, cần phân nhóm (binning) theo quy mô.
        2. **Tương quan yếu (Weak Correlation):** `response_time` và `deaths` có tương quan tuyến tính thấp (r ~ 0.04).
           *-> Ẩn số:* Mối quan hệ là phi tuyến tính, cần đào sâu vào các ngưỡng cụ thể (ví dụ: ngưỡng 24h).
        3. **Đa dạng địa lý:** Sự kiện tập trung ở Châu Á và Châu Mỹ, nơi có các "Mega-events".
        """)
        # Biểu đồ tần suất
        event_counts = df['event_type'].value_counts().reset_index()
        event_counts.columns = ['Loại', 'Số lượng']
        fig_bar = px.bar(event_counts, x='Số lượng', y='Loại', orientation='h', color='Số lượng', title="Tần suất Loại thiên tai")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- NAVIGATION BUTTON ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_n = st.columns([5, 1])
    with col_n:
        if st.button("Tiếp theo: Phân tích BQ1 ➡️", type="primary", use_container_width=True):
            navigate_to('BQ1')

def render_bq1():
    st.title("⚡ BQ1: Nghịch Lý Response Time & Giới Hạn 24h Vàng")
    st.markdown("> *Câu hỏi đặc sắc: Response time <24h có thực sự 'cứu mạng' gấp đôi không? Và nghịch lý viện trợ là gì?*")
    
    # --- DQ3.1: 24h Vàng ---
    st.subheader("📌 DQ3.1: Xác thực 'Giới Hạn 24h Vàng'")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='response_bin', y='death_rate', palette='Reds', ci=None, ax=ax)
        ax.set_title("Tỷ lệ Tử vong (%) theo Thời gian Ứng phó", fontweight='bold')
        ax.set_ylabel("Death Rate (%)")
        st.pyplot(fig)
    with c2:
        st.success("""
        **✅ Insight Thực tế (Data-driven):**
        * **<6h & 6-24h:** Tỷ lệ tử vong cực thấp (~0.004%).
        * **24-72h:** Tăng vọt lên 0.0077% (**+103%**).
        * **>72h:** Đạt 0.021% (**+440%** - Gấp 4.4 lần!).
        * **Kết luận:** 24h đầu tiên chính là "Giới hạn vàng". Chậm 1 ngày, hậu quả tăng gấp đôi.
        """)

    st.markdown("---")

    # --- DQ3.2 & DQ3.3: Địa lý & Viện trợ ---
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("📌 DQ3.2: Developed vs. Developing")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=df, x='dev_status', y='response_time_hours', palette='Set2', ax=ax)
        ax.set_title("Tốc độ phản ứng: Developed vs Developing", fontweight='bold')
        st.pyplot(fig)
        st.error("""
        **😱 Bất ngờ địa lý:**
        * **Developing Countries** (TB 10.8h) phản ứng **NHANH HƠN** Developed (TB 11.9h).
        * *Lý do:* Các nước phát triển có quy trình báo cáo phức tạp hơn, hoặc các nước đang phát triển (đặc biệt Châu Á) có kinh nghiệm thực chiến nhiều hơn.
        * Tuy nhiên, khi phản ứng chậm (>24h), Developed countries có tỷ lệ tử vong cao gấp **3.8 lần**.
        """)

    with c4:
        st.subheader("📌 DQ3.3: Nghịch lý Viện trợ (Aid)")
        # Scatter plot
        fig = px.scatter(
            df, x='response_time_hours', y='international_aid_million_usd',
            color='continent', size='deaths', hover_name='country',
            title="Response Time vs. Viện trợ (Màu=Châu lục)",
            labels={'international_aid_million_usd': 'Aid ($M)', 'response_time_hours': 'Response (h)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        st.warning("""
        **💸 Nghịch lý:**
        * Response càng nhanh (<6h) nhận được viện trợ **gấp 38 lần** nhóm chậm.
        * Châu Âu & Bắc Mỹ: Response siêu nhanh nhưng Aid gần bằng 0.
        * Châu Phi & Nam Á: Nhận Aid cao nhất nhưng tốc độ phản ứng vẫn chưa tối ưu.
        """)

    # --- ACTIONABLE INSIGHTS ---
    st.markdown("### 🚀 ACTIONABLE INSIGHTS (Đề xuất hành động)")
    st.info("""
    1.  **KPI Toàn cầu:** Thiết lập chuẩn bắt buộc: **90% sự kiện phải có đội ứng phó hiện trường <24h**.
    2.  **Fast Response Bonus:** Tạo quỹ thưởng "Càng nhanh càng nhiều tiền" -> Khuyến khích các nước đầu tư hạ tầng cảnh báo sớm thay vì chờ cứu trợ.
    3.  **Đào tạo chéo:** Developed countries cần học hỏi mô hình phản ứng nhanh tại chỗ của các nước Developing (như Việt Nam, Philippines).
    4.  **Hub Khu vực:** Xây dựng "Regional 24h Response Hub" tại Châu Phi & Nam Á để giảm response time từ 30h xuống <18h.
    """)

    # --- NAVIGATION BUTTONS ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_mid, col_n = st.columns([1, 4, 1])
    with col_p:
        if st.button("⬅️ Quay lại Tổng quan", use_container_width=True):
            navigate_to('Overview')
    with col_n:
        if st.button("Tiếp theo: Phân tích BQ2 ➡️", type="primary", use_container_width=True):
            navigate_to('BQ2')

def render_bq2():
    st.title("🇨🇳 BQ2: Nghịch Lý Quy Mô (The Scale Paradox)")
    st.markdown("> *Câu hỏi đặc sắc: Tại sao sự kiện >5 Triệu người lại được cứu nhanh hơn sự kiện nhỏ?*")

    # --- DQ1 & DQ2: Scale Paradox ---
    st.subheader("📌 DQ1 & DQ2: Quy mô càng lớn, Phản ứng càng nhanh?")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='response_time_hours', palette='Blues_d', ci=None, ax=ax)
        ax.set_title("DQ1: Response Time theo Quy mô (Mega-event nhanh nhất!)", fontweight='bold')
        ax.set_ylabel("Giờ")
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='death_rate', palette='Reds_d', ci=None, ax=ax)
        ax.set_title("DQ2: Tỷ lệ Tử vong theo Quy mô (Mega-event thấp nhất!)", fontweight='bold')
        ax.set_ylabel("Death Rate (%)")
        st.pyplot(fig)
    
    st.caption("👉 **Nghịch lý:** Mega-events (>5M người) phản ứng TB chỉ 8.2 giờ (nhanh hơn 42% so với sự kiện nhỏ) và Death Rate thấp hơn 11 lần.")

    st.markdown("---")
    
    # --- DQ4 & DQ5: Đi tìm nguyên nhân (China & India) ---
    st.subheader("📌 DQ4 & DQ5: Ai đứng sau nghịch lý này?")
    
    # Interactive Checkbox
    st.markdown("#### 🕵️‍♂️ Kiểm chứng giả thuyết:")
    exclude_giants = st.checkbox("🛑 **Loại bỏ China & India** ra khỏi dữ liệu để xem điều gì xảy ra?", value=False)

    if exclude_giants:
        df_viz = df[~df['country'].isin(['China', 'India'])]
        insight_text = "👉 **Kết quả:** Khi loại bỏ China & India, **NGHỊCH LÝ BIẾN MẤT!** Quy mô lớn không còn đồng nghĩa với phản ứng nhanh nữa."
        insight_type = st.error
    else:
        df_viz = df
        insight_text = "👉 **Hiện tại:** Dữ liệu bao gồm China & India. Họ chiếm **71%** tổng số Mega-events toàn cầu."
        insight_type = st.warning

    col3, col4 = st.columns(2)
    with col3:
        # Vẽ lại biểu đồ Response Time với dữ liệu đã lọc
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df_viz, x='scale', y='response_time_hours', palette='Greys_d', ci=None, ax=ax)
        ax.set_title(f"Response Time ({'NO China/India' if exclude_giants else 'ALL'})", fontweight='bold')
        st.pyplot(fig)
    
    with col4:
        insight_type(insight_text)
        # DQ4 Boxplot
        if not exclude_giants:
            st.markdown("**So sánh tốc độ: China+India vs Thế giới**")
            china_india_df = df[df['country'].isin(['China', 'India'])].assign(group='China & India')
            others_df = df[~df['country'].isin(['China', 'India'])].assign(group='Rest of World')
            comp_df = pd.concat([china_india_df, others_df])
            
            fig, ax = plt.subplots(figsize=(8, 3.5))
            sns.boxplot(data=comp_df, x='response_time_hours', y='group', palette='viridis', ax=ax)
            st.pyplot(fig)
            st.caption("China & India phản ứng nhanh hơn thế giới trung bình **36%**.")

    # --- ACTIONABLE INSIGHTS ---
    st.markdown("### 🚀 ACTIONABLE INSIGHTS (Đề xuất hành động)")
    st.info("""
    1.  **Học tập mô hình:** Không coi nghịch lý là lỗi dữ liệu, mà là bài học thành công. Thế giới cần học **"Mega-event Response Model"** của China & India (huy động quân đội, sơ tán diện rộng cực nhanh).
    2.  **Mega-event Playbook:** Xây dựng bộ quy chuẩn: Khi sự kiện ảnh hưởng >1M người -> Kích hoạt ngay cơ chế đặc biệt (bỏ qua thủ tục hành chính thông thường).
    3.  **Đầu tư công nghệ:** China & India dùng AI và vệ tinh rất mạnh để dự báo. Cần chuyển giao công nghệ này cho các nước nhỏ hơn để họ cũng có thể "Response like a Giant".
    """)

    # --- NAVIGATION BUTTONS ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_mid = st.columns([1, 5])
    with col_p:
        if st.button("⬅️ Quay lại BQ1", use_container_width=True):
            navigate_to('BQ1')

# --- 4. ĐIỀU HƯỚNG CHÍNH (MAIN ROUTING) ---

if df is not None:
    # Hiển thị thanh tiến trình (Optional visual cue)
    pages = ["Overview", "BQ1", "BQ2"]
    current_idx = pages.index(st.session_state['current_page'])
    st.progress((current_idx + 1) / len(pages))

    # Render trang tương ứng
    if st.session_state['current_page'] == 'Overview':
        render_overview()
    elif st.session_state['current_page'] == 'BQ1':
        render_bq1()
    elif st.session_state['current_page'] == 'BQ2':
        render_bq2()

else:
    st.stop()
