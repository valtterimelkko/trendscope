import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface RecommendedAction {
  title: string;
  description: string;
  icon: string;
  buttonLabel: string;
  onClick?: () => void;
}

interface RecommendedActionsPanelProps {
  actions?: RecommendedAction[];
}

const defaultActions: RecommendedAction[] = [
  {
    title: '🎯 Set up niche alerts',
    description: 'Get instant notifications for beauty trends',
    icon: '🎯',
    buttonLabel: 'Configure',
  },
  {
    title: '📊 Export weekly report',
    description: 'Share insights with your team',
    icon: '📊',
    buttonLabel: 'Export',
  },
];

export function RecommendedActionsPanel({ actions = defaultActions }: RecommendedActionsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">💡 Recommended</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {actions.map((action, idx) => (
          <div
            key={idx}
            className="p-4 border border-dashed border-border rounded-lg hover:border-primary/50 transition-colors"
          >
            <div className="font-medium mb-1">{action.title}</div>
            <div className="text-caption mb-3">{action.description}</div>
            <Button variant="outline" size="sm" onClick={action.onClick} className="text-xs">
              {action.buttonLabel} →
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
