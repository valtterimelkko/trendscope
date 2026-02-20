import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface QuickAction {
  label: string;
  icon: string;
  onClick?: () => void;
  href?: string;
}

interface QuickActionsPanelProps {
  actions?: QuickAction[];
}

const defaultActions: QuickAction[] = [
  { label: 'View All Trends', icon: '📊' },
  { label: 'Configure Alerts', icon: '🔔' },
  { label: 'Manage Clients', icon: '👥' },
  { label: 'Export Report', icon: '📥' },
];

export function QuickActionsPanel({ actions = defaultActions }: QuickActionsPanelProps) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-lg">⚡ Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {actions.map((action, idx) => (
            <Button
              key={idx}
              variant="outline"
              className="quick-action-btn h-auto py-4"
              onClick={action.onClick}
            >
              <span className="text-2xl">{action.icon}</span>
              <span className="text-xs font-medium text-center leading-tight">
                {action.label}
              </span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
