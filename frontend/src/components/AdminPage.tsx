import React, { useState } from 'react';
import { Upload, Button, message, Card, Space } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const AdminPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);

    try {
      const response = await axios.post('https://www.mimih2o.top/api/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      message.success('文件上传成功');
      navigate('/');
    } catch (error) {
      console.error('Upload error:', error);
      message.error('上传失败，请重试');
    }
    setLoading(false);
    return false;
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card title="数据上传" style={{ background: '#fff' }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Upload.Dragger
              name="file"
              accept=".xlsx"
              beforeUpload={handleUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 .xlsx 格式的 Excel 文件</p>
            </Upload.Dragger>
            <Button
              type="primary"
              onClick={() => navigate('/')}
              style={{ width: '100%' }}
            >
              返回查询页面
            </Button>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default AdminPage; 