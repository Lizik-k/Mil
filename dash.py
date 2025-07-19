import pandas as pd
import numpy as np
import csv
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, datetime


# Функция для создания диаграммы с приростом
def create_growth_chart(data, platform, color):
    # Создаем копию данных, чтобы не изменять исходный DataFrame
    data = data.copy()

    # Рассчитываем процентный прирост
    data[f'{platform}_прирост'] = data[platform].pct_change() * 100
    data[f'{platform}_прирост'] = data[f'{platform}_прирост'].replace([np.inf, -np.inf], np.nan)

    # Рассчитываем абсолютный прирост
    data[f'{platform}_абсолютный_прирост'] = data[platform].diff()

    # Создаем фигуру
    fig = go.Figure()

    # Добавляем столбцы с абсолютными значениями в подсказках
    fig.add_trace(go.Bar(
        x=data['Дата'],
        y=data[f'{platform}_прирост'],
        marker_color=color,
        name=f'Прирост {platform}',
        text=[f"{x:+.1f}%" if not np.isnan(x) else "" for x in data[f'{platform}_прирост']],
        textposition='outside',
        hoverinfo='text',
        hovertext=[f"Дата: {date}<br>Абсолютный прирост: {abs_change:+.0f}<br>Процентный прирост: {pct_change:+.1f}%"
                   for date, abs_change, pct_change in zip(
                data['Дата'],
                data[f'{platform}_абсолютный_прирост'],
                data[f'{platform}_прирост'])]
    ))

    # Добавляем линию тренда
    fig.add_trace(go.Scatter(
        x=data['Дата'],
        y=data[f'{platform}_прирост'],
        mode='lines+markers',
        line=dict(color='black', width=2),
        name='Тренд',
        hoverinfo='text',
        hovertext=[f"Дата: {date}<br>Процентный прирост: {pct_change:+.1f}%"
                   for date, pct_change in zip(
                data['Дата'],
                data[f'{platform}_прирост'])]
    ))

    # Настраиваем внешний вид
    fig.update_layout(
        title=f'Динамика прироста подписчиков в {platform}',
        xaxis_title='Дата',
        yaxis_title='Прирост, %',
        showlegend=True,
        plot_bgcolor='white',
        hovermode='x unified'
    )

    # Добавляем горизонтальную линию на нуле
    fig.add_hline(y=0, line_dash="dot", line_color="gray")

    return fig

# ====================== НАСТРОЙКА СТРАНИЦ ======================
st.set_page_config(

    layout="wide",  # Установка широкой рабочей области
)
if 'page' not in st.session_state:
    st.session_state.page = 'page1'  # По умолчанию первая страница

# Стили для кнопок навигации
st.markdown("""
<style>
    .nav-button {
        margin: 5px;
        padding: 10px;
        border-radius: 5px;
        width: 100%;
    }
    .nav-button.active {
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

data = pd.read_excel('Konkurent.xlsx')
konkurent = data['Конкурент']
name_konkurent = konkurent.drop_duplicates()

#
# data['Дата'] = pd.to_datetime(data['Дата'],  format='%d.%m.%Y')
data['Дата'] = pd.to_datetime(data['Дата']).dt.date


# ====================== НАВИГАЦИОННОЕ МЕНЮ ======================
cols1, cols2, cols3 = st.columns(3)
with cols1:
    if st.sidebar.button('Сравнение', key='btn_page1'):
        st.session_state.page = 'page1'
with cols2:
    if st.sidebar.button('Статистика', key='btn_page2'):
        st.session_state.page = 'page2'


# ====================== СТРАНИЦА 1 ======================
if st.session_state.page == 'page1':

    # ДАШБОРД

    st.write("""# Сравнение конкурентов""")
    #st.write("""## Версия 0.0.1""")

    st.sidebar.header('Параметры')

    # Выбор даты
    min_date = data['Дата'].min()
    max_date = data['Дата'].max()

    #
    st.sidebar.write("Выберите период:")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start = st.date_input("Начало",
                              value = min_date,
                              min_value= min_date,
                              max_value= max_date)
    with col2:
        end = st.date_input("Конец",
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date)


    konk = st.sidebar.multiselect('Конкурент', (name_konkurent), name_konkurent)


    # Применяем фильтры
    filtered_df = data[
        (data['Дата'] >= start) &
        (data['Дата'] <= end) &
        (data['Конкурент'].isin(konk))
        ]

    # Секция с метриками
    st.header('Ключевые показатели')

    # Получаем последние и предыдущие данные
    latest_date = filtered_df['Дата'].max()
    previous_date = filtered_df[filtered_df['Дата'] < latest_date]['Дата'].max()

    if pd.notna(previous_date):
        latest_data = filtered_df[filtered_df['Дата'] == latest_date]
        previous_data = filtered_df[filtered_df['Дата'] == previous_date]

        # Сравниваем данные
        comparison = pd.merge(latest_data, previous_data, on='Конкурент', suffixes=('_current', '_previous'))

        # Считаем метрики для каждой платформы
        for platform in ['ВК', 'Телеграмм', 'Инстаграмм']:
            current_col = f'{platform}_current'
            previous_col = f'{platform}_previous'

            # Общее количество подписчиков
            total_current = comparison[current_col].sum()
            total_previous = comparison[previous_col].sum()

            # Процентное изменение
            if total_previous != 0:
                pct_change = ((total_current - total_previous) / total_previous) * 100
                change_text = f"{abs(pct_change):.2f}%" #{'↑' if pct_change > 0 else '↓'}
                delta_value = round(pct_change, 2)
            else:
                pct_change = 0
                change_text = "N/A (нет предыдущих данных)"
                delta_value = None

            # Отображаем метрики
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label=f"Подписчиков в {platform}",
                    value=f"{int(total_current):,}",
                    delta=delta_value,

                    delta_color="normal"
                )
            with col2:
                # Показываем лидера по платформе
                top_competitor = comparison.loc[comparison[current_col].idxmax(), 'Конкурент']
                top_value = comparison.loc[comparison[current_col].idxmax(), current_col]
                st.metric(
                    label=f"Лидер в {platform}",
                    value=f"{top_competitor}: {int(top_value):,}"
                )

    # # Визуализация
    # st.header('Динамика подписчиков')

    # # Выбор платформы для визуализации
    # platform_to_visualize = st.selectbox(
    #     'Выберите платформу для анализа',
    #     ['ВК', 'Телеграмм', 'Инстаграмм']
    # )
    #
    # # Строим график
    # fig = px.line(
    #     filtered_df,
    #     x='Дата',
    #     y=platform_to_visualize,
    #     color='Конкурент',
    #     title=f'Динамика подписчиков в {platform_to_visualize}',
    #     labels={'Дата': 'Дата', platform_to_visualize: 'Количество подписчиков'}
    # )
    # st.plotly_chart(fig)

    # Визуализация - три отдельных графика
    st.header('Динамика подписчиков по платформам')

    # Создаем три колонки для графиков
    col1, col2, col3 = st.columns(3)

    # График для ВК
    with col1:
        fig_vk = px.line(
            filtered_df,
            x='Дата',
            y='ВК',
            color='Конкурент',
            title='Динамика в ВКонтакте',
            labels={'Дата': 'Дата', 'ВК': 'Подписчики'}
        )
        fig_vk.update_layout(
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-1.2,
                xanchor='center',
                x=0.5
            )
        )
        st.plotly_chart(fig_vk, use_container_width=True)

    # График для Телеграма
    with col2:
        fig_tg = px.line(
            filtered_df,
            x='Дата',
            y='Телеграмм',
            color='Конкурент',
            title='Динамика в Телеграме',
            labels={'Дата': 'Дата', 'Телеграмм': 'Подписчики'}
        )
        fig_tg.update_layout(
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-1.2,
                xanchor='center',
                x=0.5
            )
        )
        st.plotly_chart(fig_tg, use_container_width=True)

    # График для Инстаграма
    with col3:
        fig_inst = px.line(
            filtered_df,
            x='Дата',
            y='Инстаграмм',
            color='Конкурент',
            title='Динамика в Инстаграме',
            labels={'Дата': 'Дата', 'Инстаграмм': 'Подписчики'}
        )
        fig_inst.update_layout(
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-1.2,
                xanchor='center',
                x=0.5
            )
        )
        st.plotly_chart(fig_inst, use_container_width=True)

    # Создаем две колонки
    col1, col2 = st.columns(2)

    # Левая диаграмма - обычная столбчатая
    with col1:
        # Преобразуем данные для Plotly (длинный формат)
        df_melted = latest_data.melt(id_vars=['Конкурент'],
                                     value_vars=['ВК', 'Телеграмм', 'Инстаграмм'],
                                     var_name='Платформа',
                                     value_name='Подписчики')

        fig_bar = px.bar(
            df_melted,
            x='Конкурент',
            y='Подписчики',
            color='Платформа',
            barmode='group',
            title='Абсолютные значения подписчиков',
            labels={'Конкурент': 'Компания', 'Подписчики': 'Количество подписчиков'}
        )
        fig_bar.update_layout(
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.6,
                xanchor='center',
                x=0.5
            )
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Правая диаграмма - нормализованная
    with col2:
        # Нормализуем данные (процент от общего количества подписчиков для каждого конкурента)
        latest_data['Всего'] = latest_data[['ВК', 'Телеграмм', 'Инстаграмм']].sum(axis=1)
        latest_data['ВК_норм'] = latest_data['ВК'] / latest_data['Всего'] * 100
        latest_data['Телеграмм_норм'] = latest_data['Телеграмм'] / latest_data['Всего'] * 100
        latest_data['Инстаграмм_норм'] = latest_data['Инстаграмм'] / latest_data['Всего'] * 100

        # Преобразуем нормализованные данные
        df_norm = latest_data.melt(id_vars=['Конкурент'],
                                   value_vars=['ВК_норм', 'Телеграмм_норм', 'Инстаграмм_норм'],
                                   var_name='Платформа',
                                   value_name='Доля')

        # Улучшаем подписи платформ
        df_norm['Платформа'] = df_norm['Платформа'].replace({
            'ВК_норм': 'ВК',
            'Телеграмм_норм': 'Телеграмм',
            'Инстаграмм_норм': 'Инстаграмм'
        })

        fig_norm = px.bar(
            df_norm,
            x='Конкурент',
            y='Доля',
            color='Платформа',
            barmode='relative',
            title='Доля подписчиков по платформам (%)',
            labels={'Конкурент': 'Компания', 'Доля': 'Доля, %'}
        )
        fig_norm.update_layout(
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.6,
                xanchor='center',
                x=0.5
            ),
            yaxis=dict(range=[0, 100])  # Обеспечиваем отображение от 0 до 100%
        )
        st.plotly_chart(fig_norm, use_container_width=True)

    filtered_df = data[
        (data['Дата'] >= start) &
        (data['Дата'] <= end) &
        (data['Конкурент'].isin(konk))
        ]



if st.session_state.page == 'page2':

    # ДАШБОРД

    st.write("""# Данные по конкуренту""")
    #st.write("""## Версия 0.0.1""")

    st.sidebar.header('Параметры')

    # Выбор даты
    min_date = data['Дата'].min()
    max_date = data['Дата'].max()

    #
    st.sidebar.write("Выберите период:")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start = st.date_input("Начало",
                              value = min_date,
                              min_value= min_date,
                              max_value= max_date)
    with col2:
        end = st.date_input("Конец",
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date)


    konk = st.sidebar.selectbox('Конкурент', (name_konkurent), None)

    # Применяем фильтры
    filtered_df = data[
        (data['Дата'] >= start) &
        (data['Дата'] <= end) &
        (data['Конкурент'] == konk)
        ]

    # Секция с метриками
    st.header('Ключевые показатели')

    # Получаем последние и предыдущие данные
    latest_date = filtered_df['Дата'].max()
    previous_date = filtered_df[filtered_df['Дата'] < latest_date]['Дата'].max()

    if pd.notna(previous_date):
        latest_data = filtered_df[filtered_df['Дата'] == latest_date]
        previous_data = filtered_df[filtered_df['Дата'] == previous_date]

        # Сравниваем данные
        comparison = pd.merge(latest_data, previous_data, on='Конкурент', suffixes=('_current', '_previous'))

        colmn1, colmn2, colmn3 = st.columns(3)
        with colmn1:
            current_col = f'ВК_current'
            previous_col = f'ВК_previous'
            # Общее количество подписчиков
            total_current = comparison[current_col].sum()
            total_previous = comparison[previous_col].sum()
            # Процентное изменение
            if total_previous != 0:
                pct_change = ((total_current - total_previous) / total_previous) * 100
                change_text = f"{abs(pct_change):.2f}%"  # {'↑' if pct_change > 0 else '↓'}
                delta_value = round(pct_change, 2)
            else:
                pct_change = 0
                change_text = "N/A (нет предыдущих данных)"
                delta_value = None
            st.metric(
                label=f"Подписчиков в ВК",
                value=f"{int(total_current):,}",
                delta=delta_value,

                delta_color="normal"
            )
        with colmn2:
            current_col = f'Телеграмм_current'
            previous_col = f'Телеграмм_previous'
            # Общее количество подписчиков
            total_current = comparison[current_col].sum()
            total_previous = comparison[previous_col].sum()
            # Процентное изменение
            if total_previous != 0:
                pct_change = ((total_current - total_previous) / total_previous) * 100
                change_text = f"{abs(pct_change):.2f}%"  # {'↑' if pct_change > 0 else '↓'}
                delta_value = round(pct_change, 2)
            else:
                pct_change = 0
                change_text = "N/A (нет предыдущих данных)"
                delta_value = None
            st.metric(
                label=f"Подписчиков в Телеграмм",
                value=f"{int(total_current):,}",
                delta=delta_value,

                delta_color="normal"
            )
        with colmn3:
            current_col = f'Инстаграмм_current'
            previous_col = f'Инстаграмм_previous'
            # Общее количество подписчиков
            total_current = comparison[current_col].sum()
            total_previous = comparison[previous_col].sum()
            # Процентное изменение
            if total_previous != 0:
                pct_change = ((total_current - total_previous) / total_previous) * 100
                change_text = f"{abs(pct_change):.2f}%"  # {'↑' if pct_change > 0 else '↓'}
                delta_value = round(pct_change, 2)
            else:
                pct_change = 0
                change_text = "N/A (нет предыдущих данных)"
                delta_value = None
            st.metric(
                label=f"Подписчиков в Инстаграмм",
                value=f"{int(total_current):,}",
                delta=delta_value,

                delta_color="normal"
            )
        # Визуализация - три отдельных графика
        st.header('Динамика подписчиков по платформам')

        # Создаем три колонки для графиков
        col1, col2, col3 = st.columns(3)

        # График для ВК
        with col1:
            fig_vk = px.line(
                filtered_df,
                x='Дата',
                y='ВК',
                color='Конкурент',
                title='Динамика в ВКонтакте',
                labels={'Дата': 'Дата', 'ВК': 'Подписчики'}
            )
            fig_vk.update_layout(
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-1.2,
                    xanchor='center',
                    x=0.5
                )
            )
            st.plotly_chart(fig_vk, use_container_width=True)

        # График для Телеграма
        with col2:
            fig_tg = px.line(
                filtered_df,
                x='Дата',
                y='Телеграмм',
                color='Конкурент',
                title='Динамика в Телеграме',
                labels={'Дата': 'Дата', 'Телеграмм': 'Подписчики'}
            )
            fig_tg.update_layout(
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-1.2,
                    xanchor='center',
                    x=0.5
                )
            )
            st.plotly_chart(fig_tg, use_container_width=True)

        # График для Инстаграма
        with col3:
            fig_inst = px.line(
                filtered_df,
                x='Дата',
                y='Инстаграмм',
                color='Конкурент',
                title='Динамика в Инстаграме',
                labels={'Дата': 'Дата', 'Инстаграмм': 'Подписчики'}
            )
            fig_inst.update_layout(
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-1.2,
                    xanchor='center',
                    x=0.5
                )
            )
            st.plotly_chart(fig_inst, use_container_width=True)

        # Создаем три колонки для графиков
        col1, col2, col3 = st.columns(3)

        # График для ВК

        fig_vk = create_growth_chart(filtered_df, 'ВК', '#0068c9')
        st.plotly_chart(fig_vk, use_container_width=True)

        # График для Телеграма

        fig_tg = create_growth_chart(filtered_df, 'Телеграмм', '#83c9ff')
        st.plotly_chart(fig_tg, use_container_width=True)

        # График для Инстаграма

        fig_inst = create_growth_chart(filtered_df, 'Инстаграмм', '#fe2b2b')
        st.plotly_chart(fig_inst, use_container_width=True)
