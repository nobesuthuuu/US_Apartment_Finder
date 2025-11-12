from datetime import datetime
import plotly.io as pio
import pandas as pd
import plotly.express as px
import plotnine as pn
from shinywidgets import render_plotly
from state_choices import us_states

from shiny import reactive
from shiny.express import input, render, ui
from shiny import App

# ---------------------------------------------------------------------
# Reading in Files
# ---------------------------------------------------------------------

median_listing_price_df = pd.read_excel("cleaned_rental_data.xlsx")
df = median_listing_price_df 

# ---------------------------------------------------------------------
# Helper functions - converting to DateTime
# ---------------------------------------------------------------------
def string_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m").date()


def filter_by_date(df: pd.DataFrame, date_range: tuple):
    rng = sorted(date_range)
    dates = pd.to_datetime(df["Date"], format="%Y-%m").dt.date
    return df[(dates >= rng[0]) & (dates <= rng[1])]


# ---------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------

# Page Title and Sidebar
ui.page_opts(title= "US Apartment Finder App")

with ui.sidebar():
    # State selector
    ui.input_select("state", "Select State", choices=us_states)

    # Dynamic city selector based on state
    @render.ui
    def city_selector():
        # Filter cities based on selected state
        state_cities = sorted(df[df["State"] == input.state()]["RegionName"].dropna().unique().tolist())
        return ui.input_select("city", "Select City", choices=state_cities)

    # Dynamic comparison selector (up to 3 cities) based on state
    @render.ui
    def city_comparison_selector():
        # Filter cities based on selected state
        state_cities = sorted(df[df["State"] == input.state()]["RegionName"].dropna().unique().tolist())
        return ui.input_select(
            "compare_cities",
            "Compare Cities (select up to 3)",
            choices=state_cities,
            multiple=True,
            selected=None  # Clear selection when state changes
        )
        
    # Add helper text for comparison limit
    ui.p("Note: Maximum 3 cities can be compared")

    # input slider for date range
    min_date = string_to_date("2010-02")
    max_date = string_to_date("2019-12")

    ui.input_slider("Date", "mm-dd-yyyy", min_date, max_date,
        value = [string_to_date(dates) for dates in ["2010-02", "2019-12"]])
    
    ui.input_date_range("date_range", "Select Date Range") 
               
                

# Plotly visualization of Median Home Price Per State
ui.input_dark_mode()
custom_palette=px.colors.qualitative.Dark2
colorway= custom_palette

with ui.navset_card_underline(title = "City Median Listing Price"):


    with ui.nav_panel("Plot"):
        

        @render_plotly
        def list_price_plot():

            # Grouping by State Name and specifying the Date Columns
            price_grouped = median_listing_price_df.groupby('State').mean(numeric_only=True)     
            date_columns = median_listing_price_df.columns[6:]
            price_grouped_dates = price_grouped[date_columns].reset_index()   
            price_df_for_viz = price_grouped_dates.melt(id_vars=["State"], var_name="Date", value_name="Price($)")
            
            # Filtering by Date Range
            price_df_for_viz = filter_by_date(price_df_for_viz, input.date_range())

            if input.state() in us_states:
                price_df_for_viz = price_df_for_viz[price_df_for_viz["State"] == input.state()]
            
            else:
                df = median_listing_price_df

            # Creating Visualization using Plotly
            # adding a color palette
            color_palette = px.colors.qualitative.Plotly
            fig = px.line(price_df_for_viz, x="Date", y="Price($)", color="State")
            fig.update_layout(
                plot_bgcolor= "white",
                paper_bgcolor= "white",
                xaxis= dict(
                    showgrid= False,
                    zeroline=False,
                    title="Date",
                    titlefont=dict(size=16),
                    tickfont=dict(size=14),
                    range=[0, None]
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    title= "Rental Price($)",
                    title_font=dict(size=16),
                    tickfont=dict(size=14),
                    range=[0, None]
                )
            )
            #fig.update_xaxes(title_text="")
            #fig.update_yaxes(title_text="")

            
            return fig
        

    with ui.nav_panel("Map"):

        @render_plotly
        def state_choropleth():
            # Use the melted state-level data, filter by date range, then aggregate by state
            date_columns = median_listing_price_df.columns[6:]
            price_grouped = median_listing_price_df.groupby('State').mean(numeric_only=True)
            price_grouped_dates = price_grouped[date_columns].reset_index()
            price_df = price_grouped_dates.melt(id_vars=["State"], var_name="Date", value_name="Value")

            # Filter by selected date range and compute mean value per state across the range
            price_df = filter_by_date(price_df, input.date_range())
            state_summary = price_df.groupby('State', as_index=False)['Value'].mean()

            # Choropleth by state abbreviation
            fig = px.choropleth(
                state_summary,
                locations='State',
                locationmode='USA-states',
                color='Value',
                scope='usa',
                color_continuous_scale='Viridis',
                hover_name='State',
            )
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            return fig

    with ui.nav_panel("Compare"):

        @render_plotly
        def compare_cities_plot():
            # Melt city-level data
            date_columns = median_listing_price_df.columns[6:]
            id_vars = [c for c in median_listing_price_df.columns[:6]]
            cities_melted = median_listing_price_df.melt(id_vars=id_vars, var_name='Date', value_name='Value')

            # Filter by date range
            cities_melted = filter_by_date(cities_melted, input.date_range())

            # Filter by selected cities (enforce 3-city limit)
            selected = input.compare_cities() or []
            if selected:
                # Enforce 3-city limit
                selected = selected[:3]  # Take only first 3 selections
                cities_melted = cities_melted[cities_melted['RegionName'].isin(selected)]
                
                # Add warning if more than 3 were selected
                if len(input.compare_cities()) > 3:
                    ui.notification_show("Maximum 3 cities can be compared. Showing first 3 selections.", 
                                      duration=3000, type="warning")
            else:
                # If none selected, show the single selected city from sidebar
                if input.city():
                    cities_melted = cities_melted[cities_melted['RegionName'] == input.city()]

            fig = px.line(cities_melted, x='Date', y='Value', color='RegionName', markers=False)
            fig.update_layout(legend_title_text='City',
                              plot_bgcolor= "white",
                paper_bgcolor= "white",
                xaxis= dict(
                    showgrid= False,
                    zeroline=False,
                    title="Date",
                    titlefont=dict(size=16),
                    tickfont=dict(size=14),
                    range=[0, None]
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    title= "Rental Price($)",
                    title_font=dict(size=16),
                    tickfont=dict(size=14),
                    range=[0, None]
                )
            )
            #fig.update_xaxes(title_text='')
            #fig.update_yaxes(title_text='')
            return fig

    with ui.nav_panel("Data"):

        @render.data_frame
        def list_price_data():
            if input.state() in us_states:
                df = median_listing_price_df[median_listing_price_df["State"] == input.state()]
                        
            else:
                df = median_listing_price_df
                        
            return render.DataGrid(df)


