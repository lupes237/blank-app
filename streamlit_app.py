        # Balkendiagramm erstellen
        bar_fig = go.Figure()
        for i, row in df_tarifs_filtered.iterrows():
            bar_fig.add_trace(go.Bar(
                x=[row['Tarifname']],
                y=[row['Beitrag']],
                name=row['Anbietername'],
                marker_color=color_mapping[row['Anbietername']],
                width=0.6
            ))
        bar_fig.update_layout(title='Balkendiagramm: Tarife vergleichen',
                              xaxis_title='Tarifname',
                              yaxis_title='Beitrag in Euro',
                              xaxis_tickangle=-45,
                              width=1200,
                              height=600)
        bar_fig.update_traces(texttemplate='%{y:.2f} €', textposition='outside')  # Betrag an der Spitze der Balken anzeigen
        bar_fig.update_yaxes(tickangle=-45)  # Optionale Anpassung für die Y-Achse

        st.plotly_chart(bar_fig)

        # Liniendiagramm erstellen
        line_fig = go.Figure()
        for i, row in df_tarifs_filtered.iterrows():
            line_fig.add_trace(go.Scatter(
                x=[row['Tarifname']],
                y=[row['Beitrag']],
                mode='lines+markers',
                name=row['Anbietername'],
                line=dict(shape='linear', color=color_mapping[row['Anbietername']]),
                marker=dict(color=color_mapping[row['Anbietername']])
            ))
        line_fig.update_layout(title='Liniendiagramm: Tarife vergleichen',
                               xaxis_title='Tarifname',
                               yaxis_title='Beitrag in Euro',
                               width=1200,
                               height=600)
        line_fig.update_traces(texttemplate='%{y:.2f} €', textposition='top right')  # Betrag rechts oben anzeigen

        st.plotly_chart(line_fig)
