'use client'

interface PlanFeature {
  name: string
  included: boolean
  limit?: string
}

interface PlanComparisonCardProps {
  name: string
  description: string
  price: {
    monthly: number
    yearly: number
  }
  interval: 'month' | 'year'
  features: PlanFeature[]
  isCurrentPlan: boolean
  isPopular?: boolean
  onSelect: () => void
  disabled?: boolean
}

export function PlanComparisonCard({
  name,
  description,
  price,
  interval,
  features,
  isCurrentPlan,
  isPopular = false,
  onSelect,
  disabled = false,
}: PlanComparisonCardProps) {
  const currentPrice = interval === 'month' ? price.monthly : price.yearly
  const monthlyEquivalent = interval === 'year' ? Math.round(price.yearly / 12) : price.monthly
  const savingsPercent = interval === 'year'
    ? Math.round((1 - price.yearly / (price.monthly * 12)) * 100)
    : 0

  return (
    <div
      className={`relative rounded-2xl border ${
        isPopular
          ? 'border-blue-500 dark:border-blue-400 ring-2 ring-blue-500 dark:ring-blue-400'
          : 'border-gray-200 dark:border-gray-700'
      } bg-white dark:bg-gray-800 p-6 shadow-sm`}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center rounded-full bg-blue-500 px-3 py-1 text-xs font-semibold text-white">
            Popular
          </span>
        </div>
      )}

      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{name}</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>

        <div className="mt-4">
          <span className="text-4xl font-bold text-gray-900 dark:text-white">
            ${currentPrice}
          </span>
          <span className="text-gray-500 dark:text-gray-400">/{interval}</span>

          {interval === 'year' && (
            <p className="mt-1 text-sm text-green-600 dark:text-green-400">
              ${monthlyEquivalent}/mo · Save {savingsPercent}%
            </p>
          )}
        </div>
      </div>

      <ul className="mt-6 space-y-3">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start">
            {feature.included ? (
              <svg
                className="h-5 w-5 text-green-500 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg
                className="h-5 w-5 text-gray-400 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            <span
              className={`ml-2 text-sm ${
                feature.included
                  ? 'text-gray-700 dark:text-gray-300'
                  : 'text-gray-400 dark:text-gray-500'
              }`}
            >
              {feature.name}
              {feature.limit && (
                <span className="text-gray-500 dark:text-gray-400"> ({feature.limit})</span>
              )}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        <button
          onClick={onSelect}
          disabled={disabled || isCurrentPlan}
          className={`w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors ${
            isCurrentPlan
              ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-default'
              : isPopular
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-gray-900 dark:bg-white hover:bg-gray-800 dark:hover:bg-gray-100 text-white dark:text-gray-900'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isCurrentPlan ? 'Current Plan' : 'Select Plan'}
        </button>
      </div>
    </div>
  )
}
