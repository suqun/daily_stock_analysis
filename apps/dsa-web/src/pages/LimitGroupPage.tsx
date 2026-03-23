import { useEffect, useState, useCallback } from 'react';
import { Card, Badge, Loading, YamlViewer } from '../components/common';
import { stocksApi, type LimitGroupData, type LimitGroupStockItem } from '../api/stocks';

const renderStockList = (list: LimitGroupStockItem[], emptyTip: string) => {
  if (!list || list.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-500">
        {emptyTip}
      </div>
    );
  }
  return (
    <div className="max-h-[400px] overflow-y-auto space-y-1">
      {list.map((item) => (
        <div
          key={item.code}
          className="group flex flex-col py-2.5 px-3 rounded-lg hover:bg-gradient-to-r from-cyan/10 to-blue-500/10 transition-all duration-200 cursor-pointer border border-transparent hover:border-cyan/20"
        >
          <div className="flex justify-between items-center">
            <span className="text-sm font-mono font-medium text-cyan">{item.code}</span>
            <a
              href={`https://xueqiu.com/S/${(item.code.split('.')[1] || '') + (item.code.split('.')[0] || '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors hover:underline"
            >
              {item.name}
            </a>
          </div>
          {/* 详细信息行 */}
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
            {/* 插入时间 */}
            <span className="inline-flex items-center gap-1 text-gray-500">
              <span className="text-gray-400">📅</span>
              插入:
              <span className="font-medium text-gray-600">{item.insert_time ? item.insert_time.split(' ')[0] : '-'}</span>
            </span>
            {/* 观察天数 */}
            <span className="inline-flex items-center gap-1 text-gray-500">
              <span className="text-gray-400">🔭</span>
              观察:
              <span className={`font-medium ${(item.observe_days ?? 0) >= 3 ? 'text-amber-600' : 'text-gray-600'}`}>
                {item.observe_days ?? 0}天
              </span>
            </span>
            {/* 精选标签 */}
            {item.is_selected ? (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-50 text-green-700 rounded text-xs font-medium">
                ✓ 精选
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-100 text-gray-400 rounded text-xs">
                ○ 待观察
              </span>
            )}
          </div>
          {/* 精选时间和理由 */}
          {item.is_selected && item.selected_time && (
            <div className="mt-1 text-xs text-green-600">
              精选于 {item.selected_time.split(' ')[0]}
            </div>
          )}
          {item.selected_reason && (
            <div className="mt-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded truncate" title={item.selected_reason}>
              📝 {item.selected_reason}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const LimitGroupPage: React.FC = () => {
  const [groupData, setGroupData] = useState<LimitGroupData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.title = '涨停分组跟踪 | DSA系统';
  }, []);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await stocksApi.getLimitGroups();
      setGroupData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
    const timer = setInterval(() => {
      void loadData();
    }, 60000);
    return () => clearInterval(timer);
  }, [loadData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 text-red-600 rounded-lg text-center">
          {error}
          <button
            className="block w-full mt-2 text-sm text-red-500 hover:text-red-700"
            onClick={() => void loadData()}
          >
            点击重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold mb-1">涨停分组跟踪</h1>
        <p className="text-sm text-gray-500">
          {groupData?.update_time || '暂无更新记录'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card className="p-5 border-t-4 border-t-cyan">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">首板涨停组</h2>
            <Badge variant="info">{groupData?.first_limit_group.length || 0}只</Badge>
          </div>
          {renderStockList(groupData?.first_limit_group || [], '暂无首板涨停个股')}
        </Card>

        <Card className="p-5 border-t-4 border-t-blue-500">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">二板涨停组</h2>
            <Badge variant="history">{groupData?.second_limit_group.length || 0}只</Badge>
          </div>
          {renderStockList(groupData?.second_limit_group || [], '暂无二板涨停个股')}
        </Card>

        <Card className="p-5 border-t-4 border-t-green-500">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">精选自选股</h2>
            <Badge variant="success">{groupData?.self_select_stocks.length || 0}只</Badge>
          </div>
          {renderStockList(groupData?.self_select_stocks || [], '暂无精选自选个股')}
        </Card>
      </div>

      {/* 策略配置说明 */}
      <div className="mt-8">
        <Card className="p-5">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">涨停跟踪低吸策略配置</h2>
            <Badge variant="info">v1.0</Badge>
          </div>
          <YamlViewer
            url="/strategy/limit_up_track_dip.yaml"
            maxHeight="400px"
          />
        </Card>
      </div>
    </div>
  );
};

export default LimitGroupPage;
