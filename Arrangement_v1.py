import streamlit as st
import numpy as np
import pandas as pd
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder
import re
# from streamlit_extras.stoggle import stoggle
from streamlit_toggle import st_toggle_switch


#  card_columns = ['工步号','管理特性项目','产品标准','加工标准' ,'刀号', '刀具名称', '刀具规格/标准', '主轴转速(rpm)', '切削速度(m/min)', '进给量(m/min)']
det_columns = ['工步号','管理特性项目','产品标准','加工标准']
knife_columns = ['刀号', '刀具名称', '刀具规格/标准', '主轴转速(rpm)', '切削速度(m/min)', '进给量(m/min)']
method_columns = ['管理特性项目', '保证方法', '评价/测量技术', '规格代号', '样本容量', '样本频率']

card_columns = det_columns + method_columns[1:] + knife_columns

init_det_df = pd.DataFrame({'工步号':[1],
                      '管理特性项目':[''],
                      '产品标准':[''],
                      '加工标准':[''],
                      })   

init_knife_df = pd.read_excel('knife_lib.xlsx', sheet_name='Sheet2')
init_knife_df = init_knife_df.dropna(subset=["刀具名称"])

init_method_df = pd.read_excel('method_lib.xlsx')

if "visibility" not in st.session_state:
  st.session_state.visibility = "visible"
  st.session_state.disabled = False
  # 一些callback变量
  st.session_state.selected_idx = None
  st.session_state.card_df = None
  st.session_state.knife_df = init_knife_df
  st.session_state.knife_add = pd.DataFrame(data = [[*['待输入']*3, *['0']*3]], columns = knife_columns)
  st.session_state.method_df = init_method_df
  st.session_state.det_df = init_det_df
  st.session_state.knife_paras = [0]*6
  st.session_state.card_df = pd.DataFrame(columns = card_columns)




###########################
# 切换多个页面
###########################

class Multi_Page:
    def __init__(self):
        self.apps = []
        self.app_dict = {}

    def add_app(self, title, func):
        if title not in self.apps:
            self.apps.append(title)
            self.app_dict[title] = func

    def run(self):
        # st.title("工序工步编排实现")

        # 侧边栏显示
        st.sidebar.title(':hammer: 工序工步编排页面')
        
        title = st.sidebar.radio(
            '请在下方选择需要进入的页面：',
            self.apps )
        self.app_dict[title]() 

        st.sidebar.header('使用帮助')
        st.sidebar.info(
          '''
          本页面用于辅助识图和工步确认后的工序卡片生成，操作步骤为：

          1. **文件上传**页面上传识图编排结果
          2. **工序卡片生成**页面进行刀具选择和表格确认 
          3. **方法库**及**刀具库**可添加新方法以及新刀具
          '''
        )

        # st.sidebar.toggle('test')



###########################
# utils函数
###########################

@st.cache()
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def isNumber(input_str):
  if len(re.findall(r"\d+\.?\d*",input_str)) == 0:
    return False
  if len(re.findall(r"\d+\.?\d*",input_str)[0]) == len(input_str):
    return True
  return False


###########################
# callback函数
###########################

def update_card():
    st.session_state.card_df.loc[st.session_state.selected_idx, (knife_columns)] = st.session_state.knife_paras.copy()

def update_info_to_card():
    st.session_state.card_df[det_columns] = st.session_state.det_df[det_columns].copy()
    match_attr = method_columns[0] # 用管理特性项目进行匹配
    for  _, row in st.session_state.card_df.iterrows():  
      if row[match_attr] in st.session_state.method_df[match_attr].unique():  
          name_ = row[match_attr] 
          st.session_state.card_df.loc[(st.session_state.card_df[match_attr] == name_), method_columns[1:]] = \
            st.session_state.method_df.loc[(st.session_state.method_df[match_attr] == name_), method_columns[1:]].copy().values.tolist()

def update_knife_df():
    check_cols = ['主轴转速(rpm)', '切削速度(m/min)', '进给量(m/min)']
    for col_name in check_cols:
      if not isNumber(st.session_state.knife_add[col_name].to_numpy()[0]):
        st.warning(f'当前{col_name}列输入格式不正确，无法更新刀具参数！')
        break
    
    if isNumber(st.session_state.knife_add[col_name].to_numpy()[0]):
      st.session_state.knife_df = pd.concat([st.session_state.knife_df, st.session_state.knife_add],  ignore_index = True)


###########################
# app函数，后续可并入不同py文件函数集
###########################

def get_knife_lib():
    st.title('刀具库')
    st.markdown(':red[注意] 刀具参数中的 _主轴转速_ , _切削速度_ 以及 _进给量_ 数值仅为出现过的**参考值**，可在下方表格内进行修改')
    gb = GridOptionsBuilder.from_dataframe(st.session_state.knife_df)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    go = gb.build()
    ag = AgGrid(
            st.session_state.knife_df, 
            gridOptions=go, 
            height=400, 
            # theme = 'dark',
            enable_enterprise_modules = True,
            fit_columns_on_grid_load=True,   #列过少的时候，设置True。 列过多的时候就不用设置了
            reload_data=False
        )
    
    st.markdown('#### 添加刀具')
    st.markdown('如需添加刀具，请**完整**填写刀具信息')
    gb_add = GridOptionsBuilder.from_dataframe(st.session_state.knife_add)
    gb.configure_pagination()
    gb_add.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    go_add = gb_add.build()
    ag_add = AgGrid(
            st.session_state.knife_add, 
            gridOptions=go_add, 
            height=100, 
            # theme = 'dark',
            enable_enterprise_modules = True,
            data_return_mode=DataReturnMode.FILTERED,
            fit_columns_on_grid_load=True,   #列过少的时候，设置True。 列过多的时候就不用设置了
            reload_data=False
        )
    st.session_state.knife_add = ag_add['data']
    st.button('确认添加', on_click = update_knife_df)

def get_method_lib():
    st.title('方法库')
    gb = GridOptionsBuilder.from_dataframe(st.session_state.method_df)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    go = gb.build()
    ag = AgGrid(
            st.session_state.method_df, 
            gridOptions=go, 
            height=400, 
            # theme = 'dark',
            enable_enterprise_modules = True,
            fit_columns_on_grid_load=True,   #列过少的时候，设置True。 列过多的时候就不用设置了
            reload_data=False
        )

def get_identify_res():
  st.title('文件上传')
  st.markdown('上传识图以及编排后包含以下项目的文件：')

  col1, col2, col3, col4 = st.columns(4) 
  col1.metric("number", "工步号")
  col2.metric("string", "管理特性项目")
  col3.metric("number", "产品标准")
  col4.metric("number", "加工标准")

  st.download_button(
        label="示例模板下载",
        data=convert_df(init_det_df),
        file_name='input_template.csv',
        # mime='text/csv',
    )


  det_file = st.file_uploader('➡️请添加待工步编排文件')
  if det_file is not None:
    bytes_data = det_file.read()
    st.markdown(f'文件**{det_file.name}**已经上传完成')
    if det_file.name.endswith('.csv'):
      st.session_state.det_df = pd.read_csv(det_file)
    elif det_file.name.endswith('.xlsx'):
      st.session_state.det_df = pd.read_excel(det_file)
    else:
      st.warning('当前文件格式无法读入', icon="⚠️")
      st.session_state.det_df = init_det_df

    if st.session_state.det_df is not None:
      st.session_state.det_df['工步号'] = st.session_state.det_df['工步号'].astype('int')
      st.session_state.det_df['产品标准'] = st.session_state.det_df['产品标准'].fillna('')
      st.session_state.det_df['加工标准'] = st.session_state.det_df['加工标准'].fillna('')

    st.dataframe(st.session_state.det_df, use_container_width=True)

    if st.button('确认'):
      update_info_to_card()
      st.info('已将数据同步至工序卡片生成', icon="☑️")
    
    # to_card = st.button("切换至编排页面")
    # if to_card:
    #     switch_page('工序卡片生成')

def generate_card():
    st.title('工序卡片生成')
    st.subheader('刀具参数选择')
    col_num, col_name ,col_format= st.columns(3)
    with col_num:
        knife_number = st.selectbox(
          '请选择刀号',
          st.session_state.knife_df['刀号'].dropna().unique()
        )
    
    with col_name:
        knife_name = st.selectbox(
            "请选择刀具名称",
            st.session_state.knife_df[st.session_state.knife_df['刀号'] == knife_number]['刀具名称'].dropna().unique(),
            label_visibility=st.session_state.visibility,
            disabled=st.session_state.disabled,
        )

    with col_format:
          knife_format = st.selectbox(
              "请选择刀具规格/标准",
              st.session_state.knife_df[(st.session_state.knife_df['刀号'] == knife_number) & (st.session_state.knife_df['刀具名称'] == knife_name)]['刀具规格/标准'].dropna().unique(),
              label_visibility=st.session_state.visibility,
              disabled=st.session_state.disabled,
          )
    df_selection = st.session_state.knife_df[(st.session_state.knife_df['刀号'] == knife_number) & (st.session_state.knife_df['刀具名称'] == knife_name) & (st.session_state.knife_df['刀具规格/标准'] == knife_format)]
    
    col_1, col_2,col_3 = st.columns(3)
    with col_1:
        main_speed = st.number_input('主轴转速(rpm)',
                                  value = int(df_selection['主轴转速(rpm)'].unique()[0]),
                                  step = 100)
    with col_2:
        cut_speed = st.number_input('切削速度(m/min)',
                                  value = int(df_selection['切削速度(m/min)'].unique()[0]),
                                  step = 3) 
    with col_3:
        feed_rate = st.number_input('进给量(m/min)',
                                  value = int(df_selection['进给量(m/min)'].unique()[0]),
                                  step = 20) 
    
    st.session_state.knife_paras = [ knife_number,  knife_name, knife_format, main_speed, cut_speed ,feed_rate]
    st.button('添加刀具', on_click = update_card)

    st.subheader('管理特性项目')    
    show_all = st_toggle_switch(
          label="显示完整列名",
          key="switch_1",
          default_value=False,
          label_after=True,
          inactive_color="#D3D3D3",  # optional
          active_color="#11567f",  # optional
          track_color="#29B5E8",  # optional
      )
      
    gb = GridOptionsBuilder.from_dataframe(st.session_state.card_df)
    
    gb.configure_selection(selection_mode = 'single', use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
    go = gb.build()
    ag = AgGrid(
            data = st.session_state.card_df, 
            gridOptions=go, 
            height=400, 
            enable_enterprise_modules = True,
            # update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED,
            fit_columns_on_grid_load=(not show_all),   #列过少的时候，设置True。 列过多的时候就不用设置了
        )

    if st.button('确认当前数据'):
      st.markdown('##### **最终生成**工艺表格为')
      for col_name in [*method_columns,*knife_columns]:
        ag['data'][col_name] = ag['data'][col_name].fillna('')
      st.dataframe(ag['data'])
    # print('sp',ag['selected_rows'])
    if len(ag['selected_rows']) != 0 :
      st.session_state.selected_idx = int(ag['selected_rows'][0]['rowIndex'])
    
    csv = convert_df(st.session_state.card_df)

    def to_dxf():
      st.warning('该功能正在开发中...')

    
    st.download_button(
        label="csv格式下载当前数据",
        data=csv,
        file_name='output.csv',
        mime='text/csv',
    )
    


###########################
# main函数
###########################

st.set_page_config(page_title="工序编排页面", layout="wide")
# hide_streamlit_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             footer {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

app = Multi_Page()
app.add_app('文件上传', get_identify_res)
app.add_app('方法库', get_method_lib)
app.add_app('刀具库', get_knife_lib)
app.add_app('工序卡片生成', generate_card)
app.run()

    



# gb.configure_columns(list('abcde'), editable=True)
# resizable=True     默认可自行调整列宽 
# filterable=True    默认可进行过滤(但是我试了下，设置False，也可以过滤)
# sorteable=True     默认可自行设置排序
# editable=True      默认可以进行编辑单元格
# groupable=True     默认可以进行分组(这我没整明白什么意思)



#这个可以对原有的列进行计算，生成新的列   
# gb.configure_column('virtual column a + b', valueGetter='Number(data.a) + Number(data.b)', cellRenderer='agAnimateShowChangeCellRenderer', editable='false', type=['numericColumn'])




 
# height: int =400,
# width=None,
# fit_columns_on_grid_load: bool=False,  将调整列以适应网格加载时的网格宽度，默认情况下为 False
# update_mode: GridUpdateMode= 'value_changed' ,  # 定义gird如何将结果发送回 streamlit,可以组合使用 ：GridUpdateMode = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
# data_return_mode: DataReturnMode= 'as_input' ,  # 定义如何从组件客户端检索数据。AS_INPUT/FILTERED/FILTERED_AND_SORTED
# allow_unsafe_jscode: bool=False,          # 允许在 gridOptions 中注入 jsCode
# enable_enterprise_modules: bool=False,   #Loads Ag-Grid enterprise modules (check licensing)
# license_key: str=None,            #见上
# try_to_convert_back_to_original_types: bool=True,    #尝试将从gid检索到的数据转换为原始类型
# conversion_errors: str='coerce',     #解析失败时的行为。raise：抛出异常，coerce：设置为NaN/NaT， ignore：返回input
# reload_data:bool=False,            #用了这个，就发现，编辑单元格就是虚的，立马给你返回原来的样子。
# theme:str='light',         #streamlit、light、dark、blue、fresh、material，请大家自行测试。
# key: typing.Any=None,      #精简关键参数(懵)

    # with st.form('example form') as f:           #form表单
    #     ag = AgGrid(
    #         data, 
    #         gridOptions=go, 
    #         height=400, 
    #         enable_enterprise_modules = True,
    #         # update_mode=GridUpdateMode.MODEL_CHANGED,
    #         fit_columns_on_grid_load=True,   #列过少的时候，设置True。 列过多的时候就不用设置了
    #         reload_data=False
    #     )
    #     st.form_submit_button()                 #在这里点击提交之后，单元格里面的修改部分就可以传到后面了