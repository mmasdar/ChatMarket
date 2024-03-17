import openai
import docx2txt

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

# Set your OpenAI API key
word_doc_path = 'hasil analisis.docx'
api_key = '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'

colors = ['#287E8F', '#15CAB6', '#F6B53D', '#EF8A5A', '#E85E76', '#696CB5', '#0F488C']

def create_choropleth(data, location_col, color_col, label, color_scale):
    return px.choropleth(
        data,
        locations=location_col,
        locationmode="USA-states",
        color=color_col,
        color_continuous_scale=color_scale,
        scope="usa",
        labels={color_col: label})

def create_pie_chart(data, names_col, values_col):
    return px.pie(data, names=names_col, values=values_col, color_discrete_sequence=colors)

def create_pie_chart_with_table(data, labels_column, values_column, purchase_column):
    fig = create_pie_chart(data, labels_column, values_column)
    fig = update_piechart_with_table(fig, "Number of Consumers")

    table_data = data.rename(columns={labels_column: "Cluster", values_column: "Total Customer"})
    table_data["Total Purchase ($)"] = data[purchase_column]
    table = pd.DataFrame(table_data[["Cluster", "Total Customer", "Total Purchase ($)"]])

    return fig, table

def create_rankflow_chart(dataframe):
    def top_categories_by_season(dataframe):
        top_categories = dataframe.groupby('Season')['Category'].value_counts().groupby(level=0).nlargest(4)
        return top_categories

    # Get the top categories by season
    top_categories_season = top_categories_by_season(dataframe)

    # Create a Rankflow chart
    rankflow_data = []
    seasons = ['Fall', 'Winter', 'Spring', 'Summer']  # Define the seasons
    for season, sales_by_category in top_categories_season.groupby('Category'):
        # Reset index to avoid issues with multi-index
        sales_by_category = sales_by_category.reset_index(level='Season')
        rankflow_data.append(go.Scatter(
            x=sales_by_category['Season'].unique(),  # Extract unique values after resetting index
            y=sales_by_category['Category'],
            mode='lines+markers',
            name=season,
            line=dict(width=25)
        ))

    # Create the layout
    layout = go.Layout(
        title='Total Sales by Category in Each Season',
        xaxis=dict(title='Category'),
        yaxis=dict(title='Total Sales (pcs)')
    )

    # Create the figure
    return go.Figure(data=rankflow_data, layout=layout)


def create_spyder_chart(dataframe):
    def top_categories_by_season(dataframe):
        top_categories = dataframe.groupby(['Season', 'Item Purchased'])['Item Purchased'].count().groupby(level=0).nlargest(25)
        print(top_categories)
        top_categories = top_categories.sort_index(level=1, key=lambda x: x.str.lower())
        return top_categories

    # Get the top categories by season
    top_categories_season = top_categories_by_season(dataframe)
    # Create a Spyder chart
    spyder_data = []
    seasons = ['Fall', 'Winter', 'Spring', 'Summer']
    colors = ['blue', 'red', 'yellow', 'green']

    for i, (season, sales_by_category) in enumerate(top_categories_season.groupby(level=0)):
        spyder_data.append(go.Scatterpolar(
            r=sales_by_category.values,
            theta=sales_by_category.index.get_level_values('Item Purchased'),
            fill='toself',
            name=season,
            line_color=colors[i]
        ))

    # Create the layout
    layout = go.Layout(
        title='Spyder Chart - Total Sales by Category in Each Season',
        polar=dict(
            radialaxis=(dict(title='Total Sales (Count)'))
        ),
        showlegend=True
    )

    # Create the figure
    return go.Figure(data=spyder_data, layout=layout)

def create_line_plot(data, x_col, y_col, title):
    return px.line(data, x=x_col, y=y_col, title=title, color_discrete_sequence=[colors[2]])

def create_bar_chart(data, x_col, y_col, title):
    return px.bar(data, x=x_col, y=y_col, title=title, color=x_col, color_discrete_sequence=colors)

def plot_3d_pca(data, feature, cluster):
    scaler = StandardScaler()
    normalized_loyalty = scaler.fit_transform(data[feature])

    # Applying PCA
    pca = PCA(n_components=3)
    principal_components = pca.fit_transform(normalized_loyalty)
    principal_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2', 'PC3'])

    # Concatenating DataFrame for plotting
    final_df = pd.concat([principal_df, data[[cluster]]], axis=1)

    # Plotting in 3D using Plotly
    return px.scatter_3d(final_df, x='PC1', y='PC2', z='PC3',
                         color=cluster,
                         title='3D PCA of Clustering Results',
                         labels={'PC1': 'Principal Component 1', 'PC2': 'Principal Component 2', 'PC3': 'Principal Component 3'})

def calculate_purchase_by_cluster(df, cluster):
    result = df.groupby([cluster, 'Season'])['Purchase Amount (USD)'].sum().reset_index()
    fig = px.bar(result, x=cluster, y='Purchase Amount (USD)', color='Season', barmode='group')
    
    return fig

def update_3d_layout(fig, title='judul belum diupdate', bg_color='rgb(255, 255, 255)'):
    chart_bg_color = 'rgba(255, 255, 255, 1)'  # Define chart background color (grey)
    fig.update_layout(
        coloraxis_showscale=False,
        scene=dict(
            xaxis=dict(
                backgroundcolor=bg_color,
                gridcolor="rgb(255, 255, 255)",
                showbackground=True,
                zerolinecolor="rgb(255, 255, 255)",
            ),
            yaxis=dict(
                backgroundcolor=bg_color,
                gridcolor="rgb(255, 255, 255)",
                showbackground=True,
                zerolinecolor="rgb(255, 255, 255)",
            ),
            zaxis=dict(
                backgroundcolor=bg_color,
                gridcolor="rgb(255, 255, 255)",
                showbackground=True,
                zerolinecolor="rgb(255, 255, 255)",
            ),
        ),
        width=800,
        height=500,
        paper_bgcolor=chart_bg_color,
        title={
            'text': f"<b>{title}</b>",
            'y':0.97,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin={"t": 10, "l": 10, "r": 10, "b":5},
        showlegend=False)
    
    return fig


def update_choropleth(fig):
    land_color = "lightgrey"  # Define land color
    geo_bg_color = "white"  # Define geo background color
    chart_bg_color = 'rgba(0,0,0,0)'  # Define chart background color
    text_color = 'black'  # Define text color

    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="black",
        showland=True,
        landcolor=land_color,
        bgcolor=geo_bg_color
    )

    fig.update_layout(
        paper_bgcolor=chart_bg_color,
        plot_bgcolor=chart_bg_color,
        font_color=text_color,
        width=800,
        height=530,
        margin={"t": 10, "l": 10, "r": 10, "b":5},
        showlegend=False
    )

    return fig

def update_piechart(fig2, title='perlu update nama', height=500):
    chart_bg_color = 'rgba(255, 255, 255, 1)'  # Define chart background color (grey)
    text_color = 'black'  # Define text color

    fig2.update_layout(
        paper_bgcolor=chart_bg_color,
        plot_bgcolor=chart_bg_color,
        font_color=text_color,
        title={
            'text': f"<b>{title}</b>",
                    'y':0.96,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
        },
        width=800,
        height=height,
        margin={"t": 50, "l": 15, "r": 15, "b": 15},
        showlegend=False)  # Set showlegend to False to hide the legend

    return fig2

def update_piechart_with_table(fig2, title='perlu update nama'):
    chart_bg_color = 'rgba(255, 255, 255, 1)'  # Define chart background color (grey)
    text_color = 'black'  # Define text color

    fig2.update_layout(
        paper_bgcolor=chart_bg_color,
        plot_bgcolor=chart_bg_color,
        font_color=text_color,
        title={
            'text': f"<b>{title}</b>",
            'y':0.96,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        width=800,
        height=350,
        margin={"t": 50, "l": 15, "r": 15, "b": 15},
        showlegend=False)  # Set showlegend to False to hide the legend

    return fig2

# Fungsi untuk Halaman 'General'
def page_general(data,
                 data_biner,
                 average_purchase_amount,
                 average_review_rating,
                 average_previous_purchases,
                 total_customers, 
                 theme):

    # Implementasi khusus untuk halaman 'General'
    additional_paragraph = """
    This Dashboard has been crafted to offer a deeper understanding of customer behavior and Key Performance Indicator (KPI) analysis based on customer data. Unlock the power of this application to pinpoint customer segments, uncover trends, and gain invaluable insights into how customers engage with your business.
    """

    # Buat kotak teks dengan teks yang digabungkan
    st.sidebar.markdown(f"""<div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>""", unsafe_allow_html=True)
    st.sidebar.markdown(f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>", unsafe_allow_html=True)

    st.markdown("""<div class='big-font' style='font-size: 40px; font-weight: bold; text-align: center; margin: 0 0 0;'>Customer Clustering and KPI Dashboard</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 20px;'>General</div>""", unsafe_allow_html=True)

    customer_count_cols = st.columns(4)

    box_styles = [
        {"background-color": colors[0], "color": "white", "font-size": "20px"},
        {"background-color": colors[1], "color": "white", "font-size": "20px"},
        {"background-color": colors[2], "color": "white", "font-size": "20px"},
        {"background-color": colors[3], "color": "white", "font-size": "20px"}]

    # Update customer_info with the calculated averages
    customer_info = [
        {"top_text": "Total Customer", "bottom_text": total_customers},
        {"top_text": "Average Purchase Amount", "bottom_text": f"$ {average_purchase_amount:.2f}"},
        {"top_text": "Average Review Rating", "bottom_text": f"{average_review_rating:.2f} / 5"},
        {"top_text": "Retention Rate", "bottom_text": f"{average_previous_purchases:.2f} times"}]

    for i in range(4):
        with customer_count_cols[i]:
            st.markdown(f"<div style='{'; '.join([f'{prop}: {value}' for prop, value in box_styles[i].items()])}; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; padding: 10px; margin: 0px; height: 100px;'><div style='font-size: 14px;'>{customer_info[i]['top_text']}</div><div style='font-size: 34px; font-weight: bold; text-align: center;'>{customer_info[i]['bottom_text']}</div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 4])
    with col1:
        st.container()
        st.write("") 
        st.write("") 
        st.write("")
        cluster_option = st.selectbox("Select Cluster", ("Spending Behavior", 
                                                        "Product Preference", 
                                                        "Loyalty and Engagement",
                                                        "Payment and Shipping"))
        
        if cluster_option == "Spending Behavior":
            st.info("Identify customer segments based on their spending habits.This can help identify high spenders, bargain hunters, and occasional shoppers. Tailored marketing strategies can be developed for each group, such as exclusive offers for high spenders or targeted discounts for bargain hunters.")
            
            mode_df = data.groupby('State Abbreviation')["Cluster Spending Behavior"].agg(lambda x: x.mode()[0]).reset_index()
            fig = create_choropleth(mode_df, 'State Abbreviation', "Cluster Spending Behavior", "Cluster", "Viridis")
        
        elif cluster_option == "Product Preference":
            st.info("Group customers based on the types of products they purchase.  Understanding product preferences can assist in inventory management, personalized marketing, and product development. Identify customer segments based on their spending habits.This can help identify high spenders, bargain hunters, and occasional shoppers.")
            
            mode_df = data.groupby('State Abbreviation')["Cluster Product Preference"].agg(lambda x: x.mode()[0]).reset_index()
            fig = create_choropleth(mode_df, 'State Abbreviation', "Cluster Product Preference", "Cluster", "Viridis")
        
        elif cluster_option == "Loyalty and Engagement":
            st.info("Segment customers based on their loyalty and engagement with the brand. Identify loyal customers who can be targeted for loyalty programs and new customers who might need engagement strategies to increase their loyalty.")
                    
            mode_df = data.groupby('State Abbreviation')['Cluster Loyalty and Engagement'].agg(lambda x: x.mode()[0]).reset_index()
            fig = create_choropleth(mode_df, 'State Abbreviation', 'Cluster Loyalty and Engagement', "Cluster", "Viridis")
        
        elif cluster_option == "Payment and Shipping":
            st.info("Segment customers based on their payment and shipping preferences. This can help in optimizing payment and shipping options to enhance customer satisfaction.")
                
            mode_df = data.groupby('State Abbreviation')['Cluster Payment and Shipping'].agg(lambda x: x.mode()[0]).reset_index()
            fig = create_choropleth(mode_df, 'State Abbreviation', 'Cluster Payment and Shipping', "Cluster", "Viridis")
        
    fig = update_choropleth(fig)

    with col2:
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns([2, 1])

    with col3:
        if cluster_option == "Spending Behavior":
            feature = ['Purchase Amount (USD)', 'Previous Purchases', 'Discount Applied', 'Promo Code Used']
            cluster = 'Cluster Spending Behavior'

        elif cluster_option == "Product Preference":
            feature = ['Item Purchased', 'Category', 'Size', 'Color', 'Season']
            cluster = 'Cluster Product Preference'

        elif cluster_option == "Loyalty and Engagement":
            feature = ['Frequency of Purchases', 'Review Rating', 'Subscription Status', 'Previous Purchases']
            cluster = 'Cluster Loyalty and Engagement'

        elif cluster_option == "Payment and Shipping":
            feature = ['Payment Method', 'Shipping Type', 'Location']
            cluster = 'Cluster Payment and Shipping'

        fig3 = plot_3d_pca(data_biner, feature, cluster)
        fig3 = update_3d_layout(fig3, cluster)
        st.plotly_chart(fig3, use_container_width=True)
    

    with col4:
        if cluster_option == "Spending Behavior":
            cluster_distribution = data['Cluster Spending Behavior'].value_counts().sort_index()
            table_data = pd.DataFrame(cluster_distribution).reset_index()
            table_data.columns = ['Spending Behavior', 'Number of Consumers']
            table_data['Total Purchase ($)'] = data.groupby('Cluster Spending Behavior')['Purchase Amount (USD)'].sum().values
            fig4, table4 = create_pie_chart_with_table(table_data, 'Spending Behavior', 'Number of Consumers', 'Total Purchase ($)')

        elif cluster_option == "Product Preference":
            cluster_distribution = data['Cluster Product Preference'].value_counts().sort_index()
            table_data = pd.DataFrame(cluster_distribution).reset_index()
            table_data.columns = ['Spending Behavior', 'Number of Consumers']
            table_data['Total Purchase ($)'] = data.groupby('Cluster Product Preference')['Purchase Amount (USD)'].sum().values
            fig4, table4 = create_pie_chart_with_table(table_data, 'Spending Behavior', 'Number of Consumers', 'Total Purchase ($)')

        elif cluster_option == "Loyalty and Engagement":
            cluster_distribution = data['Cluster Loyalty and Engagement'].value_counts().sort_index()
            table_data = pd.DataFrame(cluster_distribution).reset_index()
            table_data.columns = ['Spending Behavior', 'Number of Consumers']
            table_data['Total Purchase ($)'] = data.groupby('Cluster Loyalty and Engagement')['Purchase Amount (USD)'].sum().values
            fig4, table4 = create_pie_chart_with_table(table_data, 'Spending Behavior', 'Number of Consumers', 'Total Purchase ($)')

        elif cluster_option == "Payment and Shipping":
            cluster_distribution = data['Cluster Payment and Shipping'].value_counts().sort_index()
            table_data = pd.DataFrame(cluster_distribution).reset_index()
            table_data.columns = ['Spending Behavior', 'Number of Consumers']
            table_data['Total Purchase ($)'] = data.groupby('Cluster Payment and Shipping')['Purchase Amount (USD)'].sum().values
            fig4, table4 = create_pie_chart_with_table(table_data, 'Spending Behavior', 'Number of Consumers', 'Total Purchase ($)')

        st.plotly_chart(fig4, use_container_width=True)
        st.write(table4.reset_index(drop=True))


    col6, col5 = st.columns([2, 2])
    with col5:
        if cluster_option == "Spending Behavior":
            fig = calculate_purchase_by_cluster(data,'Cluster Spending Behavior')
            st.plotly_chart(fig, use_container_width=True)

        elif cluster_option == "Product Preference":
            fig = calculate_purchase_by_cluster(data,'Cluster Product Preference')
            st.plotly_chart(fig, use_container_width=True)

        elif cluster_option == "Loyalty and Engagement":
            fig = calculate_purchase_by_cluster(data,'Cluster Loyalty and Engagement')
            st.plotly_chart(fig, use_container_width=True)

        elif cluster_option == "Payment and Shipping":
            fig = calculate_purchase_by_cluster(data,'Cluster Payment and Shipping')
            st.plotly_chart(fig, use_container_width=True)

    with col6:
        if cluster_option == "Spending Behavior":
            data = pd.melt(data_biner,
                        id_vars='Cluster Spending Behavior',
                        value_vars=['Discount Applied', 'Promo Code Used'])

            fig2 = px.box(data, x='Cluster Spending Behavior', y='value', color='variable', title='Gender Analysis')
            st.plotly_chart(fig2, use_container_width=True)

        elif cluster_option == "Product Preference":
            data = pd.melt(data_biner,
                        id_vars='Cluster Product Preference',
                        value_vars=['Item Purchased', 'Category', 'Size', 'Color', 'Season'])

            fig2 = px.box(data, x='Cluster Product Preference', y='value', color='variable', title='Gender Analysis')
            st.plotly_chart(fig2, use_container_width=True)

        elif cluster_option == "Loyalty and Engagement":
            data = pd.melt(data_biner,
                        id_vars='Cluster Loyalty and Engagement',
                        value_vars=['Frequency of Purchases', 'Review Rating', 'Subscription Status'])

            fig2 = px.box(data, x='Cluster Loyalty and Engagement', y='value', color='variable', title='Gender Analysis')
            st.plotly_chart(fig2, use_container_width=True)

        elif cluster_option == "Payment and Shipping":
            data = pd.melt(data_biner,
                        id_vars='Cluster Payment and Shipping',
                        value_vars=['Payment Method', 'Shipping Type'])

            fig2 = px.box(data, x='Cluster Payment and Shipping', y='value', color='variable', title='Gender Analysis')
            st.plotly_chart(fig2, use_container_width=True)


# Fungsi untuk Halaman 'Spending Behavior'
def page_spending_behavior(data, theme):
    # Implementasi khusus untuk halaman 'Spending Behavior'
    additional_paragraph = """
    Identify customer segments based on their spending habits.This can help identify high spenders, bargain hunters, and occasional shoppers. Tailored marketing strategies can be developed for each group, such as exclusive offers for high spenders or targeted discounts for bargain hunters.
    """
    st.sidebar.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(
    f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>",
    unsafe_allow_html=True
    )

    # Rest of your code...
    st.markdown("""
        <div class='big-font' style='font-size: 40px; font-weight: bold; text-align: center; margin: 0 0 0;'>Customer Clustering and KPI Dashboard</div>
        """, unsafe_allow_html=True)
    st.markdown(f"""
        <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 20px;'>Spending Behavior</div>
        """, unsafe_allow_html=True)

    revenue_column = 'Purchase Amount (USD)'
    cluster_column = 'Cluster Spending Behavior' 
    season_column = 'Season'

    revenue_by_cluster_season = data.groupby([cluster_column, season_column])[revenue_column].sum().reset_index()
    fig = px.bar(revenue_by_cluster_season,
                x=revenue_column,
                y=season_column,
                color=cluster_column,
                orientation='h',
                labels={revenue_column: 'Total Revenue (USD)', season_column: 'Season'},
                title='Total Revenue by Cluster and Season',
                barmode='group',
                color_discrete_sequence=['#287E8F', '#15CAB6', '#F6B53D', '#EF8A5A', '#E85E76', '#696CB5', '#0F488C'])
    fig.update_layout(coloraxis_showscale=False)

    df_grouped = data.groupby(['Category', 'Season'])['Purchase Amount (USD)'].sum().reset_index()
    fig3 = px.bar(df_grouped,
                x='Season',
                y='Purchase Amount (USD)',
                color='Category',
                barmode='group',
                labels={'Purchase Amount (USD)': 'Total Spending (USD)', 'Season': 'Season'},
                title='Total Spending per Category for Each Season',
                color_discrete_sequence=['#287E8F', '#15CAB6', '#F6B53D', '#EF8A5A', '#E85E76', '#696CB5', '#0F488C'])
    fig3.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0))

    category_sales = data.groupby('Category')['Purchase Amount (USD)'].sum().reset_index()
    fig4 = px.treemap(category_sales,
                    path=['Category'],
                    values='Purchase Amount (USD)',
                    title='Sales Across Categories',
                    color_discrete_sequence=['#287E8F', '#15CAB6', '#F6B53D', '#EF8A5A', '#E85E76', '#696CB5', '#0F488C'])

    promo_counts = data['Promo Code Used'].value_counts().reset_index()
    promo_counts = pd.DataFrame(promo_counts)
    promo_counts = promo_counts.rename(columns={'index': 'index', 'Promo Code Used': 'promo'})
    print(promo_counts)
    fig2 = px.pie(promo_counts,
                  names='promo',
                  values='count',
                  title='Total Purchases with and without Promo',
                  labels={'index': 'Promo Used', 'promo': 'Total Purchases'},
                  hole=0.5,
                  color_discrete_sequence=['#287E8F', '#15CAB6'])
        
    fig2.update_traces(textinfo='percent', insidetextorientation='horizontal')

    fig2.add_annotation(text='No Promo : $2223', x=0.5, y=0.53, font=dict(size=15, color='black'), showarrow=False)  # Percentage value
    fig2.add_annotation(text='Promo : $1677', x=0.5, y=0.47, font=dict(size=15, color='black'), showarrow=False)  # Label

    fig2.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0))

    # Create a sidebar column for the pie chart
    col1, col2 = st.columns([2, 2])

    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.plotly_chart(fig3, use_container_width=True)

    # Create a sidebar column for the pie chart
    col3, col4 = st.columns([2, 2])

    with col3:
        st.plotly_chart(fig4, use_container_width=True)
    with col4:
        st.plotly_chart(fig2, use_container_width=True)

# Fungsi untuk Halaman lainnya
def page_product_preference(data, data_biner, theme):
    # Implementasi khusus untuk halaman 'Product Preference'
    additional_paragraph = """
    Group customers based on the types of products they purchase.  Understanding product preferences can assist in inventory management, personalized marketing, and product development. Identify customer segments based on their spending habits.This can help identify high spenders, bargain hunters, and occasional shoppers. Tailored marketing strategies can be developed for each group, such as exclusive offers for high spenders or targeted discounts for bargain hunters.
    """
    st.sidebar.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(
    f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>",
    unsafe_allow_html=True
    )

    st.markdown("""
    <div class='big-font' style='font-size: 40px; font-weight: bold; text-align: center; margin: 0 0 0;'>Customer Clustering and KPI Dashboard</div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 20px;'>Product Preference</div>
    """, unsafe_allow_html=True)

    #rankflow = create_rankflow_chart(data)
    #spyder = create_spyder_chart(data)

    #fig3 = update_piechart(rankflow, 'Rankflow Total Sales in Season', 400)
    #fig4 = update_piechart(spyder, 'Product Sales')

    # Group by Season and Item Purchased, count occurrences, then find top categories
    top_item = data.groupby(['Season', 'Item Purchased'])['Item Purchased'].count().groupby(level=0).nlargest(25)
    top_item.index = top_item.index.droplevel(0)
    print(top_item)
    top_item_season = top_item.sort_index(level=1, key=lambda x: x.str.lower())

    # Create a Spyder chart
    spyder_data = []
    colors = ['blue', 'red', 'yellow', 'green']

    for i, (season, sales_by_category) in enumerate(top_item_season.groupby(level=0)):
        spyder_data.append(go.Scatterpolar(
            r=sales_by_category.values,
            theta=sales_by_category.index.get_level_values('Item Purchased'),
            fill='toself',
            name=season,
            line_color=colors[i]
        ))

    # Create the layout
    layout = go.Layout(
        title='Spyder Chart - Total Sales by Category in Each Season',
        polar=dict(
            radialaxis=(dict(title='Total Sales (Count)'))
        ),
        showlegend=True
    )

    # Create the figure
    fig4 = go.Figure(data=spyder_data, layout=layout)

    data_product = pd.melt(data_biner,
                           id_vars='Cluster Product Preference',
                           value_vars=['Item Purchased', 'Category', 'Size', 'Color', 'Season'])

    fig3 = px.box(data_product, x='Cluster Product Preference', y='value', color='variable', title='Cluster Analysis')

    cluster_distribution = data['Category'].value_counts().head(10)
    fig2 = create_pie_chart(cluster_distribution.reset_index(), 'index', 'Category')
    fig2 = update_piechart(fig2, "Top Categories")

    data_popular = data['Item Purchased'].value_counts().head(10).reset_index()
    data_popular.columns = ['Item', 'Count']
    fig = create_bar_chart(data_popular, 'Item', 'Count', 'Most Popular Items')
    fig = update_piechart(fig, 'Most Popular Items')

   # Create a sidebar column for the pie chart
    col1, col2 = st.columns([4, 1])
    with col1:
        st.plotly_chart(fig4, use_container_width=True)
    with col2:
        st.markdown('#### Top Product')
        data = data['Item Purchased'].value_counts().head(25).reset_index()
        data = pd.DataFrame(data)
        st.write(data.reset_index(drop=True))

    st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns([2, 3])
    with col3:
        st.plotly_chart(fig2, use_container_width=True)
    with col4:
        st.plotly_chart(fig, use_container_width=True)
        
def page_loyalty_and_engagement(data, theme):
    # Implementasi khusus untuk halaman 'Loyalty and Engagement'
    additional_paragraph = """
    Segment customers based on their loyalty and engagement with the brand. Identify loyal customers who can be targeted for loyalty programs and new customers who might need engagement strategies to increase their loyalty.
    """
    st.sidebar.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(
    f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>",
    unsafe_allow_html=True
    )

    st.markdown("""
    <div class='big-font' style='font-size: 40px; font-weight: bold; text-align: center; margin: 0 0 0;'>Customer Clustering and KPI Dashboard</div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 20px;'>Loyalty and Engagement</div>
    """, unsafe_allow_html=True)

    rating_variations = data['Review Rating'].value_counts()

    # Defining bins for categorization
    bins = [2.5, 2.9, 3.4, 3.9, 4.4, 5.0]
    labels = ['Very Unsatisfied', 'Unsatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']

    labels = labels[::-1]
    rating_variations_categories = pd.cut(rating_variations.index, bins=bins, labels=labels, include_lowest=True)
    df_rating_categories = pd.DataFrame({'Rating': rating_variations.index, 'Count': rating_variations.values, 'Rating Category': rating_variations_categories})
    print(df_rating_categories)
    fig = px.pie(df_rating_categories, names='Rating Category', values='Count', title='Rating Distribution', color_discrete_sequence=['#287E8F', '#15CAB6', '#F6B53D', '#EF8A5A', '#E85E76', '#696CB5', '#0F488C'], category_orders={'Rating Category': labels})
    fig.update_traces(textinfo='percent', hole=0.5)  # Setting textinfo to percent and hole to create a donut chart

    fig.add_annotation(text='61.7%', x=0.5, y=0.55, font=dict(size=24), showarrow=False)  # Percentage value
    fig.add_annotation(text='Positive', x=0.5, y=0.45, font=dict(size=14, color='gray'), showarrow=False)  # Label

    fig.update_layout(legend=dict(orientation='h', y=-0.1, x=0.3), margin=dict(l=50, r=50, b=20, t=50, pad=0))

    # Calculate total purchase amount for each frequency category
    total_purchase_by_frequency = data.groupby('Frequency of Purchases')['Purchase Amount (USD)'].sum().reset_index()

    # Create bar plot using Plotly Express
    fig3 = px.bar(total_purchase_by_frequency, 
                x='Frequency of Purchases', 
                y='Purchase Amount (USD)', 
                title='Total Purchase Amount by Frequency of Purchases Category',
                labels={'Purchase Amount (USD)': 'Total Purchase Amount (USD)'},
                color='Frequency of Purchases')

    # Update layout to remove legend
    fig3.update_layout(xaxis={'title': 'Frequency of Purchases'}, 
                    yaxis={'title': 'Total Purchase Amount (USD)'},
                    showlegend=False)  # Remove legend

    # Calculate total people per category
    total_people_per_category = data['Frequency of Purchases'].value_counts().reset_index()
    total_people_per_category.columns = ['Frequency of Purchases', 'Total People']

    # Calculate percentage of people in each category
    total_people = total_people_per_category['Total People'].sum()
    total_people_per_category['Percentage'] = (total_people_per_category['Total People'] / total_people) * 100

    # Plotting the treemap
    fig4 = px.treemap(total_people_per_category, path=['Frequency of Purchases'], values='Total People', 
                    title='Shopping Behavior - Frequency of Purchases')


    # Group data by subscription status and calculate average purchase amount
    purchase_by_subscription = data.groupby('Subscription Status')['Purchase Amount (USD)'].mean().reset_index()
    fig2 = px.bar(purchase_by_subscription, 
                y='Subscription Status', 
                x='Purchase Amount (USD)', 
                title='Average Purchase Amount by Subscription Status',
                labels={'Purchase Amount (USD)': 'Average Purchase Amount (USD)', 'Subscription Status': 'Subscription Status'},
                color='Subscription Status',
                orientation='h')  # Setting orientation to 'h' for horizontal

    fig.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0))
    fig2.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0), showlegend=False)
    fig3.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0))
    fig4.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0))

    # Create a sidebar column for the pie chart
    col1, col2 = st.columns([2, 2])

    with col1:
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        st.plotly_chart(fig, use_container_width=True)

    # Create a sidebar column for the pie chart
    col3, col4 = st.columns([3, 3])

    with col3:
        st.plotly_chart(fig2, use_container_width=True)
    with col4:
        st.plotly_chart(fig4, use_container_width=True)

def page_demographic(data, theme):
    # Implementasi khusus untuk halaman 'Demographic'
    additional_paragraph = """
    Understand customer segments based on demographic data. Tailor marketing campaigns and product offerings to suit the needs and preferences of different demographic groups.
    """
    st.sidebar.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(
    f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>",
    unsafe_allow_html=True
    )

    st.markdown("""
    <div class='big-font' style='font-size: 40px; font-weight: bold; text-align: center; margin: 0 0 0;'>Customer Clustering and KPI Dashboard</div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 20px;'>Customer Demographic</div>
    """, unsafe_allow_html=True)


    # Histogram Usia Ditumpuk untuk Gender
    fig = px.histogram(data, x="Age", color="Gender", title="Distribution of Age by Gender")

    # Pie Chart Gender
    fig2 = px.pie(data, names='Gender', title='Gender Distribution')

    # Stacked Bar Chart Category by Gender
    fig3 = px.histogram(data, x='Category', color='Gender', barmode='group', title='Category by Gender')
    fig3.update_layout(xaxis={'categoryorder':'total descending'})

    # Box Plot Age by Gender
    fig4 = px.box(data, x='Gender', y='Age', title='Age Distribution by Gender')

    # Scatter Plot Usia dan Review Rating berdasarkan Gender
    fig5 = px.scatter(data, x='Age', y='Review Rating', color='Gender', title='Age vs Review Rating by Gender')

    fig2.update_layout(legend=dict(orientation='h', y=-0.1, x=0.1), margin=dict(l=10, r=10, b=20, t=50, pad=0))
    fig2.update_layout(margin=dict(l=15, r=15, b=20, t=50, pad=0))
    
    fig.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0), showlegend=False)
    fig3.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0), showlegend=False)
    fig4.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0), showlegend=False)
    fig5.update_layout(margin=dict(l=50, r=50, b=20, t=50, pad=0), showlegend=False)

    # Create a sidebar column for the pie chart
    col1, col2 = st.columns([3, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.plotly_chart(fig4, use_container_width=True)

    # Create a sidebar column for the pie chart
    col3, col4, col5 = st.columns([1, 2, 1])

    with col3:
        st.plotly_chart(fig2, use_container_width=True)
    with col4:
        st.plotly_chart(fig5, use_container_width=True)
    with col5:
        st.plotly_chart(fig3, use_container_width=True)

def insightGPT(data, theme):
    # Implementasi khusus untuk halaman 'Demographic'
    additional_paragraph = """
    Understand customer segments based on demographic data. Tailor marketing campaigns and product offerings to suit the needs and preferences of different demographic groups.
    """
    st.sidebar.markdown(f"""
    <div class='big-font' style='font-size: 20px; text-align: center; margin: 0 0 5px;'>About the Cluster</div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(
    f"<div style='margin-top: 5px; margin-bottom: 5px; padding-left: 10px; border-left: 2px solid #333;'>{additional_paragraph}</div>",
    unsafe_allow_html=True
    )

    # Function to chat with the GPT-3 model
    def chat_with_gpt3(prompt, user_info):
        openai.api_key = api_key
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            #prompt=prompt,
            prompt=f"{user_info}\n{prompt}",
            max_tokens=200  # Adjust the number of tokens as needed
        )
        return response.choices[0].text

    text_from_doc = docx2txt.process(word_doc_path)

    # Streamlit UI
    st.title("Chat to InsightGPT")

    user_input = st.text_input("Enter your question:")

    if st.button("Ask"):
        if user_input:
            bot_response = chat_with_gpt3(user_input, text_from_doc)
            st.text("Chat MarketLLM:")
            st.write(bot_response)
        else:
            st.warning("Please enter a question.")

            
# Fungsi Utama
def main():
    # Konfigurasi halaman Streamlit
    st.set_page_config(
        page_title="Customer Segmentation Dashboard",
        page_icon="🧊",
        layout="wide",
        menu_items={'Get Help': 'https://mahaseenlab.com/',
                    'About': "# Masdar's Personal Project"},
        initial_sidebar_state="expanded")

    st.markdown("""
        <style>
            /* Main content area */
            .main {
                background-color: #f5f7fb;
                color: #33394C;
            }
         </style>
    """, unsafe_allow_html=True)

    # Pemuatan data
    file_path = r'trained model/clustered_shopping_behavior.csv'  # Update dengan path file CSV Anda
    data = pd.read_csv(file_path)

    # Data biner
    file_path_biner = r"trained model/numeric_clustered_shopping_behavior.csv"
    data_biner = pd.read_csv(file_path_biner)

    # Calculate the average of each column
    average_purchase_amount = data['Purchase Amount (USD)'].mean()
    average_review_rating = data['Review Rating'].mean()
    average_previous_purchases = data['Previous Purchases'].mean()
    total_customers = data['Customer ID'].nunique()


    # Mapping of full state names to abbreviations
    state_abbreviations = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
        'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
        'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
        'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
        'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
    }

    data['State Abbreviation'] = data['Location'].map(state_abbreviations)

    # Sidebar
    selected = None
    with st.sidebar:
        selected = option_menu("Clustering Analysis", ['General', 
                                            'Spending Behavior', 
                                            'Product Preference',
                                            'Loyalty and Engagement',
                                            'Customer Demographic',
                                            'Chat to InsightGPT'], 

                                    icons=['house', 
                                            'currency-dollar', 
                                            'basket-fill',
                                            'arrow-through-heart-fill',
                                            'truck',
                                            'globe-americas'], menu_icon="cast", default_index=0)
        #selected
    
    theme = st.sidebar.checkbox('Dark mode', key='theme')

    # Panggil fungsi berdasarkan pilihan pengguna
    if selected == 'General':
        page_general(data,
                     data_biner,
                     average_purchase_amount,
                     average_review_rating,
                     average_previous_purchases,
                     total_customers, theme)
    elif selected == 'Spending Behavior':
        page_spending_behavior(data, theme)
    elif selected == 'Product Preference':
        page_product_preference(data, data_biner, theme)
    elif selected == 'Loyalty and Engagement':
        page_loyalty_and_engagement(data, theme)
    elif selected == 'Chat to InsightGPT':
        insightGPT(data, theme)
    elif selected == 'Customer Demographic':
        page_demographic(data, theme)



# Jalankan fungsi utama
if __name__ == "__main__":
    main()
