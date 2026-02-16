'use client'

import { useMemo } from 'react'

interface CreditBalanceProps {
  balance: number
  monthlyAllowance?: number
  onTopUp: () => void
  showTopUpCta?: boolean
}

export function CreditBalance({
  balance,
  monthlyAllowance,
  onTopUp,
  showTopUpCta = true,
}: CreditBalanceProps) {
  const isLow = balance < 500
  const isEmpty = balance <= 0
  const isUnlimited = monthlyAllowance === -1

  const formatCredits = (credits: number) => {
    if (credits >= 1000000) return `${(credits / 1000000).toFixed(1)}M`
    if (credits >= 1000) return `${(credits / 1000).toFixed(1)}K`
    return credits.toString()
  }

  const statusColor = useMemo(() => {
    if (isEmpty) return 'text-red-600 dark:text-red-400'
    if (isLow) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-green-600 dark:text-green-400'
  }, [isEmpty, isLow])

  const bgColor = useMemo(() => {
    if (isEmpty) return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    if (isLow) return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
    return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
  }, [isEmpty, isLow])

  if (isUnlimited) {
    return (
      <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium text-green-800 dark:text-green-200">
              Unlimited Credits
            </span>
          </div>
          <span className="text-xs text-green-600 dark:text-green-400">
            Studio Plan
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-lg border ${bgColor} p-4`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Credit Balance</p>
          <p className={`text-2xl font-bold ${statusColor}`}>
            {formatCredits(balance)}
          </p>
          {monthlyAllowance && monthlyAllowance > 0 && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {formatCredits(monthlyAllowance)} included monthly
            </p>
          )}
        </div>

        {showTopUpCta && (
          <button
            onClick={onTopUp}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              isEmpty || isLow
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
            }`}
          >
            {isEmpty ? 'Buy Credits' : 'Top Up'}
          </button>
        )}
      </div>

      {isEmpty && (
        <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-800">
          <p className="text-sm text-red-600 dark:text-red-400">
            You're out of credits. Purchase more to continue creating content.
          </p>
        </div>
      )}

      {isLow && !isEmpty && (
        <div className="mt-3 pt-3 border-t border-yellow-200 dark:border-yellow-800">
          <p className="text-sm text-yellow-600 dark:text-yellow-400">
            Running low on credits. Consider topping up to avoid interruption.
          </p>
        </div>
      )}
    </div>
  )
}
