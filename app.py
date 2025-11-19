import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# --- CẤU HÌNH TRANG (Phải đặt đầu tiên) ---
st.set_page_config(
    page_title="Global Climate Impact Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. LOAD DATA & PREPROCESSING (Cache để chạy nhanh hơn) ---
@st.cache_data
def load_and_process_data():
    # Thay đổi đường dẫn file nếu cần thiết
    try:
        df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')
    except FileNotFoundError:
        st.error("Không tìm thấy file dữ liệu. Hãy đảm bảo file csv nằm cùng thư mục với app.py")
        return None

    # --- PREPROCESSING TỪ CODE CỦA BẠN ---
    # 1. Xử lý ngày tháng
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['year'].astype(int)

    # 2. Tạo cột Developed/Developing
    developed_countries = [
        'United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'Italy', 'Canada',
        'Australia', 'South Korea', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium',
        'Austria', 'Denmark', 'Finland', 'Norway', 'Ireland', 'New Zealand', 'Singapore'
    ]
    df['is_developed'] = df['country'].isin(developed_countries)
    df['dev_status'] = df['is_developed'].map({True: 'Developed', False: 'Developing'})

    # 3. Tạo bin Response Time
    bins_resp = [0, 6, 24, 72, np.inf]
    labels_resp = ['<6h (Siêu nhanh)', '6-24h (Nhanh)', '24-72h (Chậm)', '>72h (Rất chậm)']
    df['response_bin'] = pd.cut(df['response_time_hours'], bins=bins_resp, labels=labels_resp, include_lowest=True)

    # 4. Tính tỷ lệ
    df['death_rate'] = (df['deaths'] / df['affected_population']) * 100
    df['injury_rate'] = (df['injuries'] / df['affected_population']) * 100
    
    # 5. Tạo Scale cho Population (BQ2)
    bins_pop = [0, 100000, 1000000, 5000000, df['affected_population'].max()+1]
    labels_pop = ['<100k', '100k–1M', '1M–5M', '>5M (Mega-event)']
    df['scale'] = pd.cut(df['affected_population'], bins=bins_pop, labels=labels_pop)
    
    # 6. Log transform cho visualization phân phối
    df['log_impact'] = np.log1p(df['economic_impact_million_usd'])

    return df

df = load_and_process_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🛠️ Bộ Lọc Dữ Liệu")
    
    selected_year = st.sidebar.multiselect(
        "Chọn Năm:", options=sorted(df['year'].unique()), default=sorted(df['year'].unique())
    )
    
    selected_types = st.sidebar.multiselect(
        "Loại Thiên Tai:", options=df['event_type'].unique(), default=df['event_type'].unique()
    )
    
    selected_dev_status = st.sidebar.multiselect(
        "Nhóm Quốc Gia:", options=['Developed', 'Developing'], default=['Developed', 'Developing']
    )

    # Apply filters
    df_filtered = df[
        (df['year'].isin(selected_year)) & 
        (df['event_type'].isin(selected_types)) &
        (df['dev_status'].isin(selected_dev_status))
    ]

    # --- MAIN DASHBOARD ---
    st.title("🌍 Global Climate Events & Economic Impact Analysis")
    st.markdown("### *Từ Phân Tích Dữ Liệu đến Nghịch Lý Thực Tế*")
    
    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng Sự Kiện", f"{len(df_filtered):,}")
    c2.metric("Tổng Thiệt Hại (Triệu USD)", f"${df_filtered['economic_impact_million_usd'].sum():,.0f}")
    c3.metric("Số Người Bị Ảnh Hưởng", f"{df_filtered['affected_population'].sum():,.0f}")
    c4.metric("Số Ca Tử Vong", f"{df_filtered['deaths'].sum():,.0f}")

    st.markdown("---")

    # TABS PHÂN TÍCH
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Tổng Quan (EDA)", 
        "🚑 Nghịch Lý 72h Vàng", 
        "🏙️ Developed vs Developing", 
        "🇨🇳 Nghịch Lý Quy Mô (Scale)"
    ])

    # === TAB 1: TỔNG QUAN ===
    with tab1:
        st.subheader("1. Phân Bố Địa Lý & Loại Hình Thiên Tai")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.caption("Bản đồ phân bố thiệt hại kinh tế (Log Scale)")
            fig_map = px.scatter_geo(
                df_filtered,
                lat='latitude', lon='longitude',
                color='event_type',
                size='log_impact', # Dùng log để bong bóng không quá chênh lệch
                hover_name='country',
                hover_data=['economic_impact_million_usd', 'deaths', 'event_type'],
                projection="natural earth",
                title="Vị trí các sự kiện thiên tai"
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)

        with col2:
            st.caption("Tần suất các loại thiên tai")
            event_counts = df_filtered['event_type'].value_counts().reset_index()
            event_counts.columns = ['Event Type', 'Count']
            fig_bar = px.bar(event_counts, x='Count', y='Event Type', orientation='h', color='Count', color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.info(f"**Insight:** Dữ liệu bao gồm {df['country'].nunique()} quốc gia với {df['event_type'].nunique()} loại hình thiên tai khác nhau.")

    # === TAB 2: NGHỊCH LÝ 72H (BQ1 - Part 1) ===
    with tab2:
        st.subheader("2. Phân Tích Thời Gian Ứng Phó (Response Time)")
        st.markdown("> **Giả thuyết:** Phản ứng càng nhanh (<72h), thiệt hại về người càng thấp?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tái hiện biểu đồ BQ1
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_filtered, x='response_bin', y='death_rate', palette='Reds', ci=None, ax=ax)
            ax.set_title('Tỷ Lệ Tử Vong Theo Response Time', fontweight='bold')
            ax.set_ylabel('Tỷ lệ tử vong (%)')
            ax.set_xlabel('Thời gian ứng phó')
            st.pyplot(fig)
            
        with col2:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_filtered, x='response_bin', y='injury_rate', palette='Oranges', ci=None, ax=ax)
            ax.set_title('Tỷ Lệ Thương Tích Theo Response Time', fontweight='bold')
            ax.set_ylabel('Tỷ lệ thương tích (%)')
            ax.set_xlabel('Thời gian ứng phó')
            st.pyplot(fig)

        st.success("""
        **Insight từ code:** - Các sự kiện có phản ứng **<6h** và **6-24h** có tỷ lệ tử vong thấp hơn đáng kể.
        - Khi thời gian ứng phó vượt quá **72h**, tỷ lệ thương vong tăng vọt.
        - **Kết luận:** "72 Giờ Vàng" là hoàn toàn chính xác trong tập dữ liệu này.
        """)

    # === TAB 3: DEVELOPED vs DEVELOPING (BQ1 - Part 2 & BQ3) ===
    with tab3:
        st.subheader("3. So Sánh Nhóm Quốc Gia: Developed vs. Developing")
        st.markdown("> **Bất ngờ:** Liệu các nước phát triển có luôn làm tốt hơn?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Tỷ Lệ Tử Vong: Developing vs Developed**")
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.boxplot(data=df_filtered, x='response_bin', y='death_rate', hue='dev_status', palette='Set1', ax=ax)
            ax.set_title('Tỷ Lệ Tử Vong theo Nhóm Nước & Tốc Độ', fontsize=10)
            st.pyplot(fig)
            
        with col2:
            st.markdown("**Tốc độ phản ứng trung bình**")
            # Dùng Plotly cho Bar chart này để đổi gió
            avg_resp = df_filtered.groupby('dev_status')['response_time_hours'].mean().reset_index()
            fig_bp = px.bar(avg_resp, x='dev_status', y='response_time_hours', color='dev_status', 
                            title="Trung bình số giờ phản ứng", text_auto='.1f')
            st.plotly_chart(fig_bp, use_container_width=True)

        st.error("""
        **😱 SHOCKING INSIGHT:**
        - **Developed Countries** (Các nước phát triển) có tỷ lệ tử vong cao hơn khi phản ứng chậm!
        - **Developing Countries** (Các nước đang phát triển) lại có tốc độ phản ứng trung bình **NHANH HƠN** trong tập dữ liệu này.
        - *Lý giải:* Có thể do cơ chế báo cáo chặt chẽ hơn ở các nước phát triển, hoặc các nước đang phát triển thường xuyên đối mặt thiên tai nên có phản xạ cộng đồng tốt hơn?
        """)
        
        st.markdown("---")
        st.subheader("Mối quan hệ: Response Time vs. International Aid")
        
        # Scatter Plot BQ3
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=df_filtered, x='response_time_hours', y='international_aid_million_usd',
                        hue='dev_status', size='deaths', sizes=(20, 300), alpha=0.7, palette='Set1', ax=ax)
        ax.set_title('Response Time vs Viện Trợ (Size = Số người chết)')
        st.pyplot(fig)
        st.caption("Biểu đồ cho thấy mối tương quan yếu giữa thời gian phản ứng và viện trợ quốc tế.")

    # === TAB 4: NGHỊCH LÝ QUY MÔ (BQ2) ===
    with tab4:
        st.subheader("4. Nghịch Lý Quy Mô (Affected Population Paradox)")
        st.markdown("> **Câu hỏi:** Sự kiện quy mô càng lớn (>5M người) thì phản ứng càng chậm do quá tải? HAY NGƯỢC LẠI?")
        
        # Scale Analysis
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_filtered, x='scale', y='response_time_hours', palette='Blues_d', ci=None, ax=ax)
            ax.set_title('Response Time Theo Quy Mô', fontweight='bold')
            ax.set_ylabel("Giờ")
            st.pyplot(fig)
        
        with col2:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_filtered, x='scale', y='death_rate', palette='Reds_d', ci=None, ax=ax)
            ax.set_title('Tỷ Lệ Tử Vong Theo Quy Mô', fontweight='bold')
            ax.set_ylabel("Tỷ lệ tử vong (%)")
            st.pyplot(fig)

        st.markdown("### 🕵️ Đi tìm nguyên nhân: Vai trò của China & India")
        
        # Checkbox để bật tắt China/India
        exclude_giants = st.checkbox("Loại bỏ China & India khỏi phân tích để kiểm chứng?")
        
        if exclude_giants:
            df_temp = df_filtered[~df_filtered['country'].isin(['China', 'India'])]
            st.warning("Đã loại bỏ China và India khỏi dữ liệu.")
        else:
            df_temp = df_filtered
            st.info("Đang bao gồm China và India (Chiếm phần lớn các sự kiện Mega-event).")

        # Vẽ lại biểu đồ so sánh sau khi filter
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        sns.barplot(data=df_temp, x='scale', y='response_time_hours', ax=ax1, palette='Greys_d', ci=None)
        ax1.set_title(f'Response Time ({"NO China/India" if exclude_giants else "All"})')
        
        sns.barplot(data=df_temp, x='scale', y='death_rate', ax=ax2, palette='Greys_d', ci=None)
        ax2.set_title(f'Death Rate ({"NO China/India" if exclude_giants else "All"})')
        
        st.pyplot(fig)
        
        st.markdown("""
        **Kết luận:**
        - Khi bao gồm China & India: Các sự kiện "Mega-event" (>5M người) có tốc độ phản ứng cực nhanh và tỷ lệ tử vong thấp.
        - Khi **loại bỏ** China & India: Nghịch lý biến mất! Quy mô lớn không còn đồng nghĩa với phản ứng nhanh hơn nữa.
        => **China và India là nhân tố chính "gánh" chỉ số hiệu quả ứng phó thiên tai quy mô lớn.**
        """)

else:
    st.stop()

# Footer
st.markdown("---")
st.markdown("Designed by Your Name | Project UNKN Lab")
