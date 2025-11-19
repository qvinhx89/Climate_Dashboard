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
    initial_sidebar_state="collapsed"
)

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Overview'

def navigate_to(page):
    st.session_state['current_page'] = page
    st.rerun()

# --- 2. XỬ LÝ DỮ LIỆU ---
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
    
    # --- BQ1 Features ---
    developed_countries = [
        'United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'Italy', 'Canada',
        'Australia', 'South Korea', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium',
        'Austria', 'Denmark', 'Finland', 'Norway', 'Ireland', 'New Zealand', 'Singapore'
    ]
    df['is_developed'] = df['country'].isin(developed_countries)
    df['dev_status'] = df['is_developed'].map({True: 'Developed', False: 'Developing'})

    bins_resp = [0, 6, 24, 72, np.inf]
    labels_resp = ['<6h (Siêu tốc)', '6-24h (Nhanh)', '24-72h (Chậm)', '>72h (Rất chậm)']
    df['response_bin'] = pd.cut(df['response_time_hours'], bins=bins_resp, labels=labels_resp, include_lowest=True)

    df['death_rate'] = (df['deaths'] / df['affected_population']) * 100
    df['injury_rate'] = (df['injuries'] / df['affected_population']) * 100

    # Continent Mapping
    def get_continent(country):
        asia = ['China', 'India', 'Japan', 'South Korea', 'Indonesia', 'Philippines', 'Vietnam', 'Thailand', 'Singapore']
        europe = ['Germany', 'United Kingdom', 'France', 'Italy', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium', 'Austria', 'Poland']
        americas = ['United States', 'Canada', 'Brazil', 'Mexico', 'Argentina']
        africa = ['Nigeria', 'Egypt', 'South Africa', 'Kenya', 'Ethiopia']
        if country in asia: return 'Asia'
        if country in europe: return 'Europe'
        if country in americas: return 'Americas'
        if country in africa: return 'Africa'
        return 'Other'
    
    df['continent'] = df['country'].apply(get_continent)

    # --- BQ2 Features ---
    bins_pop = [0, 100000, 1000000, 5000000, df['affected_population'].max()+1]
    labels_pop = ['<100k', '100k–1M', '1M–5M', '>5M (Mega-event)']
    df['scale'] = pd.cut(df['affected_population'], bins=bins_pop, labels=labels_pop)

    df['log_impact'] = np.log1p(df['economic_impact_million_usd'])

    return df

df = load_and_process_data()

# --- 3. HÀM RENDER CÁC TRANG ---

def render_overview():
    st.title("🌍 Global Climate Impact Dashboard")
    st.markdown("### *Phân tích Chiến lược từ Dữ liệu Thực tế (2020-2025)*")
    
    # Row 1: KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng Sự Kiện", f"{len(df):,}")
    k2.metric("Tổng Thiệt Hại", f"${df['economic_impact_million_usd'].sum():,.0f} M")
    k3.metric("Người bị ảnh hưởng", f"{df['affected_population'].sum():,.0f}")
    k4.metric("Tốc độ Ứng phó TB", f"{df['response_time_hours'].mean():.1f} giờ")
    
    st.markdown("---")
    
    # Row 2: Map & Domain Knowledge
    st.subheader("1. Phân Bố Địa Lý & Domain Knowledge")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig_map = px.scatter_geo(
            df, lat='latitude', lon='longitude', color='event_type',
            size='log_impact', hover_name='country', projection="natural earth",
            title="Bản đồ Tác động (Size = Log Impact)"
        )
        fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    with col2:
        st.info("""
        **💡 Insight từ EDA:**
        1. **Dữ liệu lệch (Skewness):** Thiệt hại và số người chết phân phối lệch phải nghiêm trọng -> Cần xử lý Binning/Log.
        2. **Tương quan yếu:** Heatmap (bên dưới) chứng minh Response Time và Viện trợ có tương quan rất thấp.
        3. **Địa lý:** Tập trung lớn ở Châu Á (China, India) và các vùng duyên hải.
        """)
        event_counts = df['event_type'].value_counts().reset_index()
        event_counts.columns = ['Loại', 'Số lượng']
        fig_bar = px.bar(event_counts, x='Số lượng', y='Loại', orientation='h', title="Tần suất Loại thiên tai")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Row 3: Top 15 Countries & Heatmap
    st.subheader("2. Top Quốc Gia & Tương Quan Biến Số")
    c3, c4 = st.columns(2)
    
    with c3:
        top15 = df['country'].value_counts().head(15).reset_index()
        top15.columns = ['Quốc gia', 'Số sự kiện']
        fig_top15 = px.bar(
            top15, x='Số sự kiện', y='Quốc gia', orientation='h', 
            color='Số sự kiện', color_continuous_scale='plasma',
            title="Top 15 Quốc gia có tần suất sự kiện cao nhất"
        )
        fig_top15.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top15, use_container_width=True)

    with c4:
        st.markdown("**Heatmap Tương Quan (Pearson)**")
        key_cols = ['economic_impact_million_usd', 'deaths', 'injuries', 
                    'affected_population', 'response_time_hours', 'international_aid_million_usd']
        corr_matrix = df[key_cols].corr()
        fig_corr, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5, ax=ax)
        ax.set_title("Tương quan giữa các biến số chính")
        st.pyplot(fig_corr)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_n = st.columns([5, 1])
    with col_n:
        if st.button("Tiếp theo: Phân tích BQ1 ➡️", type="primary", use_container_width=True):
            navigate_to('BQ1')

def render_bq1():
    st.title("⚡ BQ1: Nghịch Lý Response Time & Giới Hạn 24h Vàng")
    
    # DQ3.1
    st.subheader("📌 DQ3.1: Xác thực 'Giới Hạn 24h Vàng'")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='response_bin', y='death_rate', palette='Reds', ci=None, ax=ax)
        ax.set_title("Tỷ lệ Tử vong (%) theo Thời gian Ứng phó", fontweight='bold')
        st.pyplot(fig)
    with c2:
        st.success("""
        **✅ Insight Thực tế:** 24h đầu tiên là "Giới hạn vàng".
        * **<24h:** Tỷ lệ tử vong thấp ổn định (~0.004%).
        * **>72h:** Tăng vọt lên 0.021% (**gấp 4.4 lần** so với mức thấp nhất).
        """)

    st.markdown("---")

    # DQ3.2 & DQ3.3
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("📌 DQ3.2: Developed vs. Developing")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=df, x='dev_status', y='response_time_hours', palette='Set2', ax=ax)
        ax.set_title("Tốc độ: Developing NHANH HƠN Developed", fontweight='bold')
        st.pyplot(fig)
        st.error("**Nghịch lý:** Developed countries phản ứng chậm hơn và khi chậm (>24h), họ chịu tổn thất nhân mạng cao gấp 3.8 lần.")

    with c4:
        st.subheader("📌 DQ3.3: Nghịch lý Viện trợ")
        fig = px.scatter(
            df, x='response_time_hours', y='international_aid_million_usd',
            color='continent', size='deaths', hover_name='country',
            title="Response Time vs. Viện trợ (Màu=Châu lục)"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.warning("**Nghịch lý:** Response càng nhanh (<6h) nhận được viện trợ càng nhiều.")

    st.info("🚀 **ACTION:** KPI 90% sự kiện <24h | Quỹ thưởng Fast Response | Đào tạo chéo cho Developed countries.")

    # Navigation
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
    
    st.subheader("📌 DQ1 & DQ2: Quy mô càng lớn, Phản ứng càng nhanh?")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='response_time_hours', palette='Blues_d', ci=None, ax=ax)
        ax.set_title("DQ1: Response Time (Mega-event nhanh nhất!)", fontweight='bold')
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='death_rate', palette='Reds_d', ci=None, ax=ax)
        ax.set_title("DQ2: Death Rate (Mega-event thấp nhất!)", fontweight='bold')
        st.pyplot(fig)
    
    st.markdown("---")
    
    # DQ4 & DQ5: Checkbox logic
    st.subheader("📌 DQ4 & DQ5: Ai đứng sau nghịch lý này?")
    
    st.markdown("#### 🕵️‍♂️ Kiểm chứng giả thuyết:")
    exclude_giants = st.checkbox("🛑 **Loại bỏ China & India** ra khỏi dữ liệu?", value=False)

    if exclude_giants:
        df_viz = df[~df['country'].isin(['China', 'India'])]
        insight_text = "👉 **Kết quả:** Loại bỏ China & India -> **Nghịch lý BIẾN MẤT!** Mega-events không còn nhanh nữa."
        insight_type = st.error
    else:
        df_viz = df
        insight_text = "👉 **Hiện tại:** Dữ liệu bao gồm China & India (Chiếm 71% Mega-events)."
        insight_type = st.warning

    col3, col4 = st.columns(2)
    with col3:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df_viz, x='scale', y='response_time_hours', palette='viridis', ci=None, ax=ax)
        ax.set_title(f"Response Time ({'NO China/India' if exclude_giants else 'ALL'})", fontweight='bold')
        ax.set_ylabel("Giờ")
        st.pyplot(fig)
    
    with col4:
        insight_type(insight_text)
        if not exclude_giants:
            st.markdown("**So sánh: China+India vs Thế giới**")
            china_india_df = df[df['country'].isin(['China', 'India'])].assign(group='China & India')
            others_df = df[~df['country'].isin(['China', 'India'])].assign(group='Rest of World')
            comp_df = pd.concat([china_india_df, others_df])
            
            fig, ax = plt.subplots(figsize=(8, 3.5))
            sns.boxplot(data=comp_df, x='response_time_hours', y='group', palette='magma', ax=ax)
            st.pyplot(fig)
            st.caption("China & India nhanh hơn thế giới trung bình 36%.")

    st.info("🚀 **ACTION:** Học mô hình 'Mega-event Response' của China/India | Áp dụng công nghệ dự báo sớm cho các nước nhỏ.")

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_mid, col_n = st.columns([1, 4, 1])
    with col_p:
        if st.button("⬅️ Quay lại BQ1", use_container_width=True):
            navigate_to('BQ1')
    with col_n:
        if st.button("Tiếp theo: Kết luận & Khuyến nghị 🏁", type="primary", use_container_width=True):
            navigate_to('Conclusion')

def render_conclusion():
    st.title("🏁 Tổng Kết & Khuyến Nghị Chiến Lược")
    st.markdown("### *Bức tranh toàn cảnh: Từ dữ liệu đến hành động thực tiễn*")

    # 1. Summary Metrics (Tóm tắt lại các số liệu ấn tượng nhất)
    st.markdown("#### 🏆 Top Key Insights (Số liệu ấn tượng nhất)")
    c1, c2, c3 = st.columns(3)
    c1.metric(label="Quy tắc 24h Vàng", value="-52% Deaths", delta="Nếu phản ứng <24h")
    c2.metric(label="China & India Factor", value="36% Faster", delta="So với thế giới", delta_color="normal")
    c3.metric(label="Developed Risk", value="+3.8x Deaths", delta="Khi phản ứng chậm >24h", delta_color="inverse")

    st.markdown("---")

    # 2. Performance Matrix (Biểu đồ mới - Rất quan trọng)
    st.subheader("📊 Ma Trận Hiệu Quả Quốc Gia (Performance Matrix)")
    st.markdown("""
    *Biểu đồ này gom nhóm tất cả các quốc gia để tìm ra ai đang hoạt động hiệu quả nhất.*
    * **Trục hoành (X):** Tốc độ phản ứng TB (Càng về bên trái càng tốt).
    * **Trục tung (Y):** Tỷ lệ tử vong TB (Càng thấp càng tốt).
    """)

    # Data prep cho Scatter Plot tổng hợp
    country_perf = df.groupby(['country', 'dev_status', 'continent']).agg({
        'response_time_hours': 'mean',
        'death_rate': 'mean',
        'event_id': 'count',
        'economic_impact_million_usd': 'sum'
    }).reset_index()
    
    # Lọc bớt các nước có ít sự kiện để biểu đồ đỡ rối (chỉ lấy nước > 5 sự kiện)
    country_perf = country_perf[country_perf['event_id'] > 5]

    fig_matrix = px.scatter(
        country_perf, 
        x="response_time_hours", 
        y="death_rate",
        size="event_id", 
        color="dev_status", 
        hover_name="country",
        text="country", # Hiển thị tên nước
        log_y=True, # Log scale cho death rate để dễ nhìn
        title="Performance Matrix: Response Speed vs. Death Rate (Log Scale)",
        labels={"response_time_hours": "Avg Response Time (Hours)", "death_rate": "Avg Death Rate (%)"}
    )
    
    # Thêm đường tham chiếu
    fig_matrix.add_vline(x=24, line_dash="dash", line_color="red", annotation_text="Ngưỡng 24h")
    fig_matrix.update_traces(textposition='top center')
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.success("""
    **🎯 Phân tích Ma trận:**
    * **Góc dưới bên trái (Lý tưởng):** Các nước phản ứng nhanh và chết ít (thường là China, India, một số nước Đông Á).
    * **Góc trên bên phải (Nguy hiểm):** Các nước phản ứng chậm và tỷ lệ tử vong cao.
    * **Nghịch lý Developed:** Nhiều nước phát triển nằm rải rác ở vùng giữa, cho thấy sự thiếu ổn định trong ứng phó thảm họa lớn.
    """)

    st.markdown("---")

    # 3. Final Checklist (Hành động)
    st.subheader("🚀 Lộ Trình Hành Động (Strategic Roadmap)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Ngắn hạn (0-12 tháng)")
        st.checkbox("Thiết lập KPI quốc gia: **Response Time < 24h** cho 90% sự kiện.", value=True)
        st.checkbox("Kích hoạt quỹ thưởng **'Fast Response Bonus'**.", value=True)
        st.checkbox("Ban hành **'Mega-event Playbook'** dựa trên mô hình China/India.", value=True)
    
    with col2:
        st.markdown("#### Dài hạn (1-3 năm)")
        st.checkbox("Xây dựng **Regional Hubs** tại Châu Phi & Nam Á.", value=False)
        st.checkbox("Chuyển giao công nghệ vệ tinh/AI dự báo cho các nước nhỏ.", value=False)
        st.checkbox("Tái cấu trúc quy trình khẩn cấp tại các đô thị lớn ở Developed Countries.", value=False)

    # Navigation Start Over
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Quay về Trang chủ (Overview)", type="secondary", use_container_width=True):
        navigate_to('Overview')

# --- 4. ROUTING ---
if df is not None:
    pages = ["Overview", "BQ1", "BQ2", "Conclusion"]
    current_idx = pages.index(st.session_state['current_page'])
    st.progress((current_idx + 1) / len(pages))

    if st.session_state['current_page'] == 'Overview':
        render_overview()
    elif st.session_state['current_page'] == 'BQ1':
        render_bq1()
    elif st.session_state['current_page'] == 'BQ2':
        render_bq2()
    elif st.session_state['current_page'] == 'Conclusion':
        render_conclusion()
else:
    st.stop()
