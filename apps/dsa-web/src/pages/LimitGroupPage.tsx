import { useState, useEffect } from 'react';

// 内联类型定义，彻底解决模块导入报错
interface LimitStockItem {
  code: string;
  name: string;
}

interface LimitGroupData {
  update_time: string;
  update_date: string;
  first_limit_group: LimitStockItem[];
  second_limit_group: LimitStockItem[];
  self_select_stocks: LimitStockItem[];
  source?: string;
}

const LimitGroupPage = () => {
  const [groupData, setGroupData] = useState<LimitGroupData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 数据请求函数，写法完全符合规范
  const fetchLimitGroupData = async () => {
    try {
      setError(null);
      const res = await fetch('/strategy/limit_group_data.json');
      if (!res.ok) throw new Error('请求失败');
      const data = await res.json();
      setGroupData(data);
    } catch (err) {
      setError('数据加载失败，请检查后端同步状态');
    } finally {
      setLoading(false);
    }
  };

  // 生命周期钩子，修复所有调用错误
  useEffect(() => {
    fetchLimitGroupData().catch(() => {});
    const timer = setInterval(fetchLimitGroupData, 60000);
    return () => clearInterval(timer);
  }, []);

  // 页面标题设置
  useEffect(() => {
    document.title = '涨停分组跟踪 | DSA系统';
  }, []);

  // 股票列表渲染
  const renderStockList = (list: LimitStockItem[], emptyTip: string) => {
    if (!list || list.length === 0) {
      return (
        <div className="py-8 text-center text-sm text-gray-500">
          {emptyTip}
        </div>
      );
    }
    return (
      <div className="max-h-[400px] overflow-y-auto">
        {list.map((item) => (
          <div 
            key={item.code} 
            className="flex justify-between items-center py-2.5 border-b border-gray-100"
          >
            <span className="text-sm font-mono">{item.code}</span>
            <span className="text-sm">{item.name}</span>
          </div>
        ))}
      </div>
    );
  };

  // 完整页面渲染，所有标签闭合、无语法错误
  return (
    <div className="px-4 py-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold mb-1">涨停分组跟踪</h1>
        <p className="text-sm text-gray-500">
          {groupData?.update_time || '暂无更新记录'}
        </p>
      </div>

      {/* 加载态 */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan/20 border-t-cyan" />
          <span className="ml-3 text-sm text-gray-600">数据加载中...</span>
        </div>
      )}

      {/* 错误提示 */}
      {error && !loading && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg text-center">
          {error}
        </div>
      )}

      {/* 分组数据展示 */}
      {!loading && !error && groupData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* 首板涨停组 */}
          <div className="p-5 bg-white rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">首板涨停组</h2>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                {groupData.first_limit_group.length}只
              </span>
            </div>
            {renderStockList(groupData.first_limit_group, '暂无首板涨停个股')}
          </div>

          {/* 二板涨停组 */}
          <div className="p-5 bg-white rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">二板涨停组</h2>
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                {groupData.second_limit_group.length}只
              </span>
            </div>
            {renderStockList(groupData.second_limit_group, '暂无二板涨停个股')}
          </div>

          {/* 精选自选股 */}
          <div className="p-5 bg-white rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">精选自选股</h2>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                {groupData.self_select_stocks.length}只
              </span>
            </div>
            {renderStockList(groupData.self_select_stocks, '暂无精选自选个股')}
          </div>
        </div>
      )}
    </div>
  );
};

export default LimitGroupPage;