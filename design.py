"""Shared design choices for the gold dashboard."""

# Each country keeps one colour on every chart.
COUNTRY_COLOURS = {
    "China": "#B5392F",
    "China / HK": "#B5392F",
    "Russia": "#3A5BA0",
    "India": "#D29A2E",
    "Turkey": "#8E4A9E",
    "UK / US": "#5B6770",
}
OTHER_COLOUR = "#BDBAB2"

GOLD = "#A8822A"
ETF_GREY = "#5B6770"
ESTIMATE_DASH = "dash"

FONT = "Source Sans Pro, sans-serif"
PAPER = "rgba(0,0,0,0)"


def colour_for(name: str) -> str:
    """Return a country's colour, or neutral grey for countries without one."""
    return COUNTRY_COLOURS.get(name, OTHER_COLOUR)


def style(fig, height=380):
    """Apply the shared chart style to a Plotly figure."""
    fig.update_layout(
        height=height,
        font_family=FONT,
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)")
    return fig
