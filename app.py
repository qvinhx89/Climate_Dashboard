import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# --- 0. CẤU HÌNH & LOAD DATA ---
st.set_page_config(
    page_title="Climate Impact Dashboard",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')
    except:
        st.error("Lỗi: Không tìm thấy file 'global_climate_events_economic_impact_2020_2025.csv'")
        return None

    # Preprocessing cơ bản
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['year'].astype(int)
    
    # Tạo biến Developed/Developing
    developed_countries = [
        'United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'Italy', 'Canada',
        'Australia', 'South Korea', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium',
        'Austria', 'Denmark', 'Finland', 'Norway', 'Ireland', 'New Zealand', 'Singapore'
    ]
    df['is_developed'] = df['country'].isin(developed_countries)
    df['dev_status'] = df['is_developed'].map({True: 'Developed', False: 'Developing'})

    # Preprocessing cho BQ1 (Response Time)
    bins_resp = [0, 6, 24, 72, np.inf]
    labels_resp = ['<6h (Siêu nhanh)', '6-24h (Nhanh)', '24-72h (Chậm)', '>72h (Rất chậm)']
    df['response_bin'] = pd.cut(df['response_time_hours'], bins=bins_resp, labels=labels_resp, include_lowest=True)
    df['death_rate'] = (df['deaths'] / df['affected_population']) * 100
    df['injury_rate'] = (df['injuries'] / df['affected_population']) * 100

    # Preprocessing cho BQ2 (Scale)
    bins_pop = [0, 100000, 1000000, 5000000, df['affected_population'].max()+1]
    labels_pop = ['<100k', '100k–1M', '1M–5M', '>5M (Mega-event)']
    df['scale'] = pd.cut(df['affected_population'], bins=bins_pop, labels=labels_pop)
    
    # Log transform cho EDA
    df['log_impact'] = np.log1p(df['economic_impact_million_usd'])
    
    return df

df = load_data()

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.title("⚙️ Bộ lọc")
    years = st.sidebar.multiselect("Năm", sorted(df['year'].unique()), default=sorted(df['year'].unique()))
    types = st.sidebar.multiselect("Loại thiên tai", df['event_type'].unique(), default=df['event_type'].unique())
    
    # Lọc dữ liệu
    df_sub = df[(df['year'].isin(years)) & (df['event_type'].isin(types))]

    st.title("🌍 Dashboard Phân Tích Tác Động Khí Hậu Toàn Cầu")
    st.markdown("---")

    # --- PHẦN 1: TỔNG QUAN & EDA ---
    st.header("1️⃣ Tổng Quan & Khám Phá Dữ Liệu (EDA)")
    
    # 1.1 KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng sự kiện", f"{len(df_sub):,}")
    k2.metric("Thiệt hại kinh tế", f"${df_sub['economic_impact_million_usd'].sum():,.0f} M")
    k3.metric("Người bị ảnh hưởng", f"{df_sub['affected_population'].sum():,.0f}")
    k4.metric("Thời gian ứng phó TB", f"{df_sub['response_time_hours'].mean():.1f} giờ")

    # 1.2 Phân phối (EDA)
    st.subheader("🔍 Domain Knowledge từ EDA")
    col_eda1, col_eda2 = st.columns(2)
    
    with col_eda1:
        # Histograms
        st.markdown("**Phân phối dữ liệu (Log-transformed)**")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.histplot(df_sub['log_impact'], kde=True, ax=ax, color='teal')
        ax.set_title("Phân phối thiệt hại kinh tế (Log Scale)")
        st.pyplot(fig)
    
    with col_eda2:
        st.info("""
        **💡 Insight rút ra từ bước EDA:**
        1. **Dữ liệu lệch phải (Right-skewed):** Hầu hết các biến số (thiệt hại, số người chết) không phân phối chuẩn.
           -> *Hành động:* Cần sử dụng Log-transform khi chạy mô hình hồi quy.
        2. **Tần suất vs Tác động:** Biểu đồ tần suất (Countplot) cho thấy bão/lũ lụt xảy ra nhiều nhất, nhưng Heatmap tương quan cho thấy số người chết không phụ thuộc tuyến tính vào viện trợ quốc tế (r rất thấp).
        """)

    with st.expander("Xem thêm biểu đồ Tần suất & Heatmap Tương quan"):
        c1, c2 = st.columns(2)
        with c1:
            # --- SỬA LỖI TẠI ĐÂY ---
            # Bước 1: Tính toán và reset index
            event_counts = df_sub['event_type'].value_counts().reset_index()
            
            # Bước 2: Đặt tên cột cụ thể để tránh lỗi version Pandas
            # Cột 0 là loại thiên tai, Cột 1 là số lượng
            event_counts.columns = ['Loại thiên tai', 'Số lượng'] 
            
            # Bước 3: Vẽ biểu đồ với tên cột mới
            fig = px.bar(event_counts, x='Số lượng', y='Loại thiên tai', 
                         title="Tần suất theo loại thiên tai", orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            corr = df_sub[['economic_impact_million_usd', 'deaths', 'response_time_hours', 'international_aid_million_usd']].corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
            st.pyplot(fig)

    st.markdown("---")

    # --- PHẦN 2: BQ1 - RESPONSE TIME PARADOX ---
    st.header("2️⃣ BQ1: Yếu Tố Thời Gian Ứng Phó & Nghịch Lý Phát Triển")
    st.markdown("*Business Question: Tốc độ ứng phó ảnh hưởng thế nào đến thiệt hại nhân mạng? Các nước giàu có làm tốt hơn không?*")

    # DQ1: 72h Vàng
    st.subheader("📌 DQ1: Có tồn tại quy tắc '72 Giờ Vàng' không?")
    col_bq1_1, col_bq1_2 = st.columns(2)
    with col_bq1_1:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=df_sub, x='response_bin', y='death_rate', palette='Reds', ci=None, ax=ax)
        ax.set_title("Tỷ lệ Tử vong theo Thời gian ứng phó")
        st.pyplot(fig)
    with col_bq1_2:
        st.success("""
        **✅ Kết luận:** CÓ.
        - Nhóm **<6h** và **6-24h** có tỷ lệ tử vong thấp nhất.
        - Sau **72h**, tỷ lệ tử vong tăng vọt.
        
        **🚀 Hành động:**
        - Thiết lập hệ thống cảnh báo sớm để đảm bảo đội cứu hộ có mặt trong 24h đầu.
        """)

    # DQ2: Developed vs Developing
    st.subheader("📌 DQ2: Các nước phát triển (Developed) có tỷ lệ tử vong thấp hơn không?")
    col_bq1_3, col_bq1_4 = st.columns(2)
    with col_bq1_3:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.boxplot(data=df_sub, x='response_bin', y='death_rate', hue='dev_status', palette='Set1', ax=ax)
        ax.set_title("So sánh: Developed vs Developing")
        st.pyplot(fig)
    with col_bq1_4:
        st.error("""
        **😱 Nghịch lý:** KHÔNG HẲN.
        - Ở các mức phản ứng chậm (>24h), các nước **Developed** lại có tỷ lệ tử vong cao hơn bất thường.
        - Các nước **Developing** phản ứng trung bình nhanh hơn (có thể do quen với thiên tai?).
        
        **🚀 Hành động:**
        - Các nước phát triển cần xem lại quy trình ứng phó khẩn cấp khi sự kiện kéo dài.
        """)

    # DQ3: Aid vs Response
    st.subheader("📌 DQ3: Phản ứng chậm có nhận được nhiều viện trợ hơn không?")
    st.markdown(f"Correlation: **{df_sub['response_time_hours'].corr(df_sub['international_aid_million_usd']):.4f}** (Gần như bằng 0)")
    fig = px.scatter(df_sub, x="response_time_hours", y="international_aid_million_usd", 
                     color="dev_status", size="deaths", hover_name="country",
                     title="Response Time vs Viện trợ (Size = Số người chết)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")

    # --- PHẦN 3: BQ2 - SCALE PARADOX ---
    st.header("3️⃣ BQ2: Nghịch Lý Quy Mô (The Scale Paradox)")
    st.markdown("*Business Question: Sự kiện quy mô càng lớn (Mega-events) thì càng hỗn loạn và chậm trễ?*")

    # DQ4: Scale vs Response
    st.subheader("📌 DQ4: Quy mô dân số bị ảnh hưởng tác động thế nào đến tốc độ ứng phó?")
    
    col_bq2_1, col_bq2_2 = st.columns(2)
    with col_bq2_1:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=df_sub, x='scale', y='response_time_hours', palette='Blues_d', ci=None, ax=ax)
        ax.set_title("Tốc độ ứng phó theo Quy mô")
        st.pyplot(fig)
    with col_bq2_2:
        st.warning("""
        **🤔 Quan sát:**
        - Sự kiện >5M người (Mega-event) lại có tốc độ ứng phó **NHANH NHẤT**.
        - Nghe có vẻ vô lý vì quy mô lớn thường gây tắc nghẽn.
        -> *Cần đào sâu xem quốc gia nào chi phối nhóm này.*
        """)

    # DQ5: China & India Factor
    st.subheader("📌 DQ5: Ai đứng sau nghịch lý này?")
    
    # Checkbox tương tác quan trọng
    remove_giants = st.checkbox("🛑 Loại bỏ China & India khỏi dữ liệu để kiểm chứng?", value=False)
    
    if remove_giants:
        data_viz = df_sub[~df_sub['country'].isin(['China', 'India'])]
        st.caption("Đang hiển thị dữ liệu: **Thế giới (Trừ China & India)**")
    else:
        data_viz = df_sub
        st.caption("Đang hiển thị dữ liệu: **Toàn cầu (Bao gồm China & India)**")

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots()
        sns.barplot(data=data_viz, x='scale', y='response_time_hours', palette='Greys_d', ci=None, ax=ax)
        ax.set_title(f"Response Time ({'NO China/India' if remove_giants else 'ALL'})")
        st.pyplot(fig)
    with c2:
        st.info("""
        **💡 Insight Cốt Lõi:**
        - **China & India** chiếm đa số các sự kiện Mega-event và họ phản ứng rất nhanh.
        - Khi **loại bỏ** 2 nước này, biểu đồ bên trái thay đổi hoàn toàn: Quy mô lớn không còn nhanh nữa.
        
        **🚀 Hành động chiến lược:**
        - Các tổ chức quốc tế nên nghiên cứu mô hình ứng phó thiên tai diện rộng của China & India để áp dụng cho các quốc gia đông dân khác.
        """)

else:
    st.stop()
