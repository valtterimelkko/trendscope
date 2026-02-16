'use client'

interface CreditPackCardProps {
  id: string
  name: string
  credits: number
  price: number
  badge?: string
  onPurchase: (packId: string) => void
  isLoading?: boolean
}

export function CreditPackCard({
  id,
  name,
  credits,
  price,
  badge,
  onPurchase,
  isLoading = false,
}: CreditPackCardProps) {
  const pricePerCredit = (price / credits) * 100 // cents per credit * 100 for better display
  const formattedPrice = (price / 100).toFixed(2) // Convert cents to dollars

  const formatCredits = (num: number) => {
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`
    return num.toString()
  }

  return (
    <div className={`relative rounded-xl border ${badge ? 'border-blue-500 ring-2 ring-blue-500' : 'border-gray-200 dark:border-gray-700'} bg-white dark:bg-gray-800 p-5 transition-shadow hover:shadow-md`}>
      {badge && (
        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center rounded-full bg-blue-500 px-2.5 py-0.5 text-xs font-semibold text-white">
            {badge}
          </span>
        </div>
      )}

      <div className="text-center">
        <p className="text-3xl font-bold text-gray-900 dark:text-white">
          {formatCredits(credits)}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">credits</p>

        <div className="mt-3">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            ${formattedPrice}
          </span>
        </div>

        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          ${(pricePerCredit / 100).toFixed(4)} per credit
        </p>
      </div>

      <button
        onClick={() => onPurchase(id)}
        disabled={isLoading}
        className={`mt-4 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors ${
          badge
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-900 dark:bg-white hover:bg-gray-800 dark:hover:bg-gray-100 text-white dark:text-gray-900'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {isLoading ? 'Processing...' : 'Purchase'}
      </button>
    </div>
  )
}
