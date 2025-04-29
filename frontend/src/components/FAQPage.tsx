import React from 'react';
import { Card, Typography, Collapse, Space, Divider, Row, Col } from 'antd';
import { QuestionCircleOutlined, SearchOutlined, FilterOutlined, DownloadOutlined, CalendarOutlined, UploadOutlined, FileExcelOutlined, ExclamationCircleOutlined, SettingOutlined, LockOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

const FAQPage: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card 
        bordered={false}
        style={{ 
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
          background: 'linear-gradient(to bottom, #ffffff, #f9f9f9)'
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ 
            textAlign: 'center', 
            marginBottom: '32px',
            padding: '20px 0',
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            borderRadius: '8px',
            color: 'white'
          }}>
            <Title level={2} style={{ color: 'white', marginBottom: '8px' }}>
              <QuestionCircleOutlined style={{ marginRight: '12px' }} />
              常见问题解答
            </Title>
            <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: '16px' }}>
              以下是自助查询工具使用过程中常见的问题及解答，如有其他问题，请联系管理员。
            </Paragraph>
          </div>

          <Row gutter={[24, 24]}>
            <Col xs={24} md={12}>
              <Card 
                title={
                  <span>
                    <SearchOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                    查询相关
                  </span>
                }
                bordered={false}
                style={{ 
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  height: '100%'
                }}
              >
                <Collapse defaultActiveKey={['1']} ghost>
                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        如何查询机构信息？
                      </Text>
                    } 
                    key="1"
                  >
                    <Paragraph>
                      在"按机构查询"标签页中，输入机构号或机构名称，点击搜索按钮即可查询。支持精确匹配，请输入完整的机构号或机构名称。
                    </Paragraph>
                  </Panel>

                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        如何查询商户信息？
                      </Text>
                    } 
                    key="2"
                  >
                    <Paragraph>
                      在"按商户查询"标签页中，输入商户号或商户名称，点击搜索按钮即可查询。商户号支持精确匹配，商户名称支持模糊匹配。
                    </Paragraph>
                  </Panel>

                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        如何筛选交易笔数小于10的商户？
                      </Text>
                    } 
                    key="3"
                  >
                    <Paragraph>
                      在查询结果页面，点击"仅显示笔数&lt;10"按钮，系统会自动筛选出有效交易笔数小于10的商户。
                    </Paragraph>
                  </Panel>

                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        如何导出查询结果？
                      </Text>
                    } 
                    key="4"
                  >
                    <Paragraph>
                      在查询结果页面，点击"导出Excel"按钮，系统会自动将当前查询结果导出为Excel文件。如果已应用筛选，导出的将是筛选后的结果。
                    </Paragraph>
                  </Panel>

                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        数据日期是什么意思？
                      </Text>
                    } 
                    key="5"
                  >
                    <Paragraph>
                      数据日期表示当前系统中数据的更新日期，即数据的最新时间点。系统会定期更新数据，数据日期也会相应更新。
                    </Paragraph>
                  </Panel>
                </Collapse>
              </Card>
            </Col>

            <Col xs={24} md={12}>
              <Card 
                title={
                  <span>
                    <SettingOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                    系统相关
                  </span>
                }
                bordered={false}
                style={{ 
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  height: '100%'
                }}
              >
                <Collapse defaultActiveKey={['6']} ghost>
                 


                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        查询结果为空怎么办？
                      </Text>
                    } 
                    key="8"
                  >
                    <Paragraph>
                      如果查询结果为空，请检查输入的信息是否正确。系统会显示数据库中的总记录数，如果总记录数为0，可能是数据尚未上传或数据有问题。
                    </Paragraph>
                  </Panel>

                  <Panel 
                    header={
                      <Text strong>
                        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        如何调整每页显示的数量？
                      </Text>
                    } 
                    key="9"
                  >
                    <Paragraph>
                      在查询结果页面底部，可以选择每页显示的记录数，默认为10条，可选择20、50、100条。
                    </Paragraph>
                  </Panel>

                
                </Collapse>
              </Card>
            </Col>
          </Row>

          <Divider />

          <div style={{ 
            textAlign: 'center', 
            padding: '20px',
            background: '#f5f5f5',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <Title level={4} style={{ marginBottom: '8px' }}>
              <ExclamationCircleOutlined style={{ marginRight: '8px', color: '#faad14' }} />
              需要更多帮助？
            </Title>
            <Paragraph>
              如果您在使用过程中遇到其他问题，请联系系统管理员获取支持。
            </Paragraph>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default FAQPage; 