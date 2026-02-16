export function EmptyState({
  title,
  description,
  icon,
  action,
}: {
  title: string;
  description: string;
  icon?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center">
      {icon && <div className="mb-4 text-6xl">{icon}</div>}
      <h3 className="mb-2 text-xl font-semibold text-gray-900">{title}</h3>
      <p className="mb-6 max-w-md text-sm text-gray-600">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
