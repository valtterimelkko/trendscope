'use client'

import { useMemo } from 'react'

interface TrialBannerProps {
  trialEndsAt: Date
  onUpgrade: () => void
  planName?: string
}

export function TrialBanner({ trialEndsAt, onUpgrade, planName = 'Pro' }: TrialBannerProps) {
  const daysRemaining = useMemo(() => {
    const now = new Date()
    const diff = trialEndsAt.getTime() - now.getTime()
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
  }, [trialEndsAt])

  const isUrgent = daysRemaining <= 3
  const isExpired = daysRemaining === 0

  if (isExpired) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm font-medium text-red-800 dark:text-red-200">
                Your trial has expired
              </p>
              <p className="text-sm text-red-700 dark:text-red-300">
                Subscribe now to continue using {planName} features
              </p>
            </div>
          </div>
          <button
            onClick={onUpgrade}
            className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            Subscribe Now
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`${isUrgent ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500' : 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'} border-l-4 p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <svg className={`h-5 w-5 ${isUrgent ? 'text-yellow-500' : 'text-blue-500'} mr-3`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
          <div>
            <p className={`text-sm font-medium ${isUrgent ? 'text-yellow-800 dark:text-yellow-200' : 'text-blue-800 dark:text-blue-200'}`}>
              {daysRemaining} day{daysRemaining !== 1 ? 's' : ''} left in your {planName} trial
            </p>
            <p className={`text-sm ${isUrgent ? 'text-yellow-700 dark:text-yellow-300' : 'text-blue-700 dark:text-blue-300'}`}>
              {isUrgent ? 'Don\'t lose access to your data!' : 'Enjoying the trial? Subscribe to keep your features.'}
            </p>
          </div>
        </div>
        <button
          onClick={onUpgrade}
          className={`ml-4 px-4 py-2 ${isUrgent ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'} text-white text-sm font-medium rounded-md transition-colors`}
        >
          Upgrade Now
        </button>
      </div>
    </div>
  )
}
