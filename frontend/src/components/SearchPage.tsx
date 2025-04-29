import React, { useState, useEffect } from 'react';
import { Input, Table, Button, Space, Card, Tabs, message, Upload, Modal, Form } from 'antd';
import { SearchOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { TablePaginationConfig } from 'antd/es/table';

const { Search } = Input;
const { TabPane } = Tabs;

// 设置axios默认配置
axios.defaults.baseURL = 'http://localhost:8000';

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 清除token并重定向到登录页
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

interface Merchant {
  merchant_id: string;
  merchant_name: string;
  institution: string;
  institution_id: string;
  transaction_count: number;
}

interface ApiResponse {
  items: Merchant[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  data_date?: string;
}

const SearchPage: React.FC = () => {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [loading, setLoading] = useState(false);
  const [showLessThan10, setShowLessThan10] = useState(false);
  const [searchType, setSearchType] = useState<'institution' | 'merchant'>('institution');
  const [searchValue, setSearchValue] = useState('');
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filteredTotal, setFilteredTotal] = useState(0);
  const [apiTotal, setApiTotal] = useState(0);
  const [allMerchants, setAllMerchants] = useState<Merchant[]>([]);
  const [dataDate, setDataDate] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoginModalVisible, setIsLoginModalVisible] = useState(false);
  const [loginForm] = Form.useForm();

  // 获取数据日期
  const fetchDataDate = async () => {
    try {
      console.log('开始获取数据日期');
      const response = await axios.get('http://localhost:8000/api/data-date');
      console.log('获取数据日期响应:', response.data);
      if (response.data && response.data.date) {
        console.log('设置数据日期为:', response.data.date);
        setDataDate(response.data.date);
      } else {
        console.log('数据日期为空，设置为未设置');
        setDataDate('未设置');
      }
    } catch (error) {
      console.error('获取数据日期失败:', error);
      setDataDate('未设置');
    }
  };

  // 在组件加载时获取数据日期
  useEffect(() => {
    console.log('组件加载，获取数据日期');
    fetchDataDate();
  }, []);

  // 检查登录状态
  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  // 处理登录
  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      const response = await axios.post('/api/login/', values);
      localStorage.setItem('token', response.data.token);
      setIsLoggedIn(true);
      setIsAdmin(response.data.is_admin || false);
      setIsLoginModalVisible(false);
      message.success('登录成功');
    } catch (error) {
      message.error('登录失败，请检查用户名和密码');
    }
  };

  // 处理登出
  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setIsAdmin(false);
    message.success('已登出');
  };

  // 处理文件上传
  const handleUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post('/api/upload/', formData);
      message.success('文件上传成功');
      
      // 更新数据日期
      if (response.data.data_date && response.data.data_date !== "未更新") {
        setDataDate(response.data.data_date);
        console.log('从上传响应更新数据日期:', response.data.data_date);
      }
      
      // 刷新数据
      if (searchValue) {
        handleSearch(searchValue);
      }
      
      // 重新获取数据日期，确保显示最新值
      fetchDataDate();
      
      return false; // 阻止默认上传行为
    } catch (error: any) {
      if (error.response && error.response.status === 401) {
        setIsLoginModalVisible(true);
      } else {
        message.error('上传失败，请重试');
      }
      return false;
    }
  };

  const columns = [
    {
      title: '商户号',
      dataIndex: 'merchant_id',
      key: 'merchant_id',
    },
    {
      title: '商户名称',
      dataIndex: 'merchant_name',
      key: 'merchant_name',
    },
    {
      title: '机构',
      dataIndex: 'institution',
      key: 'institution',
    },
    {
      title: '机构号',
      dataIndex: 'institution_id',
      key: 'institution_id',
    },
    {
      title: '有效交易笔数',
      dataIndex: 'transaction_count',
      key: 'transaction_count',
    },
  ];

  const handleSearch = async (value: string, page: number = 1, pageSize: number = pagination.pageSize) => {
    if (!value.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    setSearchValue(value);
    setLoading(true);
    try {
      console.log('Searching for:', value);
      const params: any = {
        page: page,
        page_size: pageSize
      };
      
      if (searchType === 'institution') {
        // 机构查询：同时匹配机构号和机构名称
        params.institution_id = value;
        params.institution = value;
        params.merchant_id = null;
        params.merchant_name = null;
      } else {
        // 商户查询：同时匹配商户号和商户名称
        params.merchant_id = value;
        params.merchant_name = value;
        params.institution_id = null;
        params.institution = null;
      }

      // 先获取所有数据
      const allDataParams = { ...params, page_size: 1000 }; // 设置一个足够大的页面大小以获取所有数据
      const allDataResponse = await axios.get(`http://localhost:8000/api/merchants/`, { params: allDataParams });
      const allData = allDataResponse.data as ApiResponse;
      
      // 保存所有查询结果
      setAllMerchants(allData.items);
      
      // 根据筛选条件设置显示的数据
      if (showLessThan10) {
        const filtered = allData.items.filter(m => m.transaction_count < 10);
        setMerchants(filtered);
        setFilteredTotal(filtered.length);
      } else {
        setMerchants(allData.items);
        setFilteredTotal(allData.items.length);
      }
      
      // 保存API返回的总数
      setApiTotal(allData.total);
      
      // 更新分页状态
      setPagination({
        current: 1,
        pageSize: pageSize,
        total: showLessThan10 ? filteredTotal : allData.total,
      });

      if (allData.items.length === 0) {
        message.info(`未找到匹配的${searchType === 'institution' ? '机构' : '商户'}数据，请尝试其他关键词`);
      } else {
        message.success(`找到 ${allData.total} 条记录`);
      }
    } catch (error) {
      console.error('Search error:', error);
      message.error('查询失败，请稍后重试');
    }
    setLoading(false);
  };

  // 处理搜索框搜索
  const handleSearchInput = (value: string) => {
    handleSearch(value);
  };

  // 处理表格分页变化
  const handleTableChange = (pagination: TablePaginationConfig) => {
    if (pagination.current && pagination.pageSize) {
      // 更新分页状态
      setPagination({
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: showLessThan10 ? filteredTotal : apiTotal,
      });
    }
  };

  // 处理每页条数变化
  const handlePageSizeChange = (current: number, size: number) => {
    // 更新分页状态
    setPagination(prev => ({
      ...prev,
      current: 1, // 重置到第一页
      pageSize: size,
      total: showLessThan10 ? filteredTotal : apiTotal,
    }));
  };

  const handleExport = () => {
    const data = merchants.map(merchant => ({
      '商户号': merchant.merchant_id,
      '商户名称': merchant.merchant_name,
      '机构': merchant.institution,
      '机构号': merchant.institution_id,
      '有效交易笔数': merchant.transaction_count,
    }));

    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '商户数据');
    XLSX.writeFile(wb, '商户数据.xlsx');
  };

  // 处理筛选按钮点击
  const handleFilterChange = () => {
    const newShowLessThan10 = !showLessThan10;
    setShowLessThan10(newShowLessThan10);
    
    // 从所有查询结果中筛选
    if (newShowLessThan10) {
      const filtered = allMerchants.filter(m => m.transaction_count < 10);
      setMerchants(filtered);
      setFilteredTotal(filtered.length);
    } else {
      setMerchants(allMerchants);
      setFilteredTotal(allMerchants.length);
    }
    
    // 重置到第一页
    setPagination(prev => ({
      ...prev,
      current: 1,
      total: newShowLessThan10 ? filteredTotal : apiTotal,
    }));
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ width: '100%' }} />
              <Space>
                {isLoggedIn && isAdmin && (
                  <Upload
                    beforeUpload={handleUpload}
                    showUploadList={false}
                  >
                    <Button type="primary" icon={<UploadOutlined />}>上传数据</Button>
                  </Upload>
                )}
              </Space>
            </div>
            
            <Tabs 
              activeKey={searchType} 
              onChange={(key) => {
                setSearchType(key as 'institution' | 'merchant');
                setMerchants([]); // 切换查询类型时清空结果
                setSearchValue(''); // 清空搜索值
              }}
            >
              <TabPane tab="按机构查询" key="institution">
                <Search
                  placeholder="输入机构号或机构名称（如：杨庄、3411463939）"
                  allowClear
                  enterButton={<SearchOutlined />}
                  size="large"
                  onSearch={handleSearchInput}
                  style={{ width: '100%' }}
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                />
              </TabPane>
              <TabPane tab="按商户查询" key="merchant">
                <Search
                  placeholder="输入商户号或商户名称（如：1012017062111201、宿州市埇桥区孟亮理发店）"
                  allowClear
                  enterButton={<SearchOutlined />}
                  size="large"
                  onSearch={handleSearchInput}
                  style={{ width: '100%' }}
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                />
              </TabPane>
            </Tabs>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space size="middle">
                <Button
                  type={showLessThan10 ? 'primary' : 'default'}
                  onClick={handleFilterChange}
                >
                  {showLessThan10 ? '显示全部' : '仅显示笔数<10'}
                </Button>
                <span style={{ 
                  color: '#666', 
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  marginLeft: '8px'
                }}>
                  数据日期：{dataDate || '加载中...'}
                </span>
              </Space>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExport}
                disabled={merchants.length === 0}
              >
                导出Excel
              </Button>
            </div>
          </Space>
        </Card>

        <Card>
          <Table
            columns={columns}
            dataSource={merchants}
            rowKey="merchant_id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: showLessThan10 ? filteredTotal : apiTotal,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total) => `共 ${total} 条记录`,
              onChange: (page, pageSize) => handlePageSizeChange(page, pageSize)
            }}
            onChange={handleTableChange}
          />
        </Card>
      </Space>

      <Modal
        title="登录"
        visible={isLoginModalVisible}
        onCancel={() => setIsLoginModalVisible(false)}
        footer={null}
      >
        <Form
          form={loginForm}
          onFinish={handleLogin}
          layout="vertical"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SearchPage; 