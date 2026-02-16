'use client'

import { useState, useMemo } from 'react'

interface SeatManagementProps {
  currentSeats: number
  maxSeats: number
  pricePerSeat: number
  interval: 'month' | 'year'
  daysRemaining: number
  onUpdateSeats: (newCount: number) => Promise<void>
}

export function SeatManagement({
  currentSeats,
  maxSeats,
  pricePerSeat,
  interval,
  daysRemaining,
  onUpdateSeats,
}: SeatManagementProps) {
  const [pendingSeats, setPendingSeats] = useState(currentSeats)
  const [isUpdating, setIsUpdating] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const seatDiff = pendingSeats - currentSeats
  const isUnlimited = maxSeats === -1

  const estimatedProration = useMemo(() => {
    if (seatDiff <= 0) return 0
    // Estimate: (price per seat / days in period) * days remaining * seats added
    const daysInPeriod = interval === 'month' ? 30 : 365
    const dailyRate = pricePerSeat / daysInPeriod
    return Math.round(dailyRate * daysRemaining * seatDiff)
  }, [seatDiff, pricePerSeat, interval, daysRemaining])

  const handleUpdateSeats = async () => {
    if (pendingSeats === currentSeats) return

    setIsUpdating(true)
    try {
      await onUpdateSeats(pendingSeats)
      setShowConfirm(false)
    } finally {
      setIsUpdating(false)
    }
  }

  const formatPrice = (cents: number) => {
    return (cents / 100).toFixed(2)
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Team Seats
      </h3>

      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {currentSeats}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {isUnlimited ? 'seats (unlimited)' : `of ${maxSeats} seats`}
          </p>
        </div>

        <div className="text-right">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            ${formatPrice(pricePerSeat)}/seat/{interval}
          </p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            ${formatPrice(currentSeats * pricePerSeat)}/{interval}
          </p>
        </div>
      </div>

      {/* Seat selector */}
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={() => setPendingSeats(Math.max(1, pendingSeats - 1))}
          disabled={pendingSeats <= 1 || isUpdating}
          className="w-10 h-10 rounded-full border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>

        <div className="flex-1 text-center">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {pendingSeats}
          </span>
          <span className="text-gray-500 dark:text-gray-400 ml-2">seats</span>
        </div>

        <button
          onClick={() => setPendingSeats(Math.min(isUnlimited ? 999 : maxSeats, pendingSeats + 1))}
          disabled={(pendingSeats >= maxSeats && !isUnlimited) || isUpdating}
          className="w-10 h-10 rounded-full border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Proration preview */}
      {seatDiff !== 0 && (
        <div className={`rounded-lg p-4 mb-4 ${seatDiff > 0 ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-green-50 dark:bg-green-900/20'}`}>
          {seatDiff > 0 ? (
            <>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Adding {seatDiff} seat{seatDiff !== 1 ? 's' : ''}
              </p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Prorated charge today: ~${formatPrice(estimatedProration)}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                Next billing: ${formatPrice(pendingSeats * pricePerSeat)}/{interval}
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                Removing {Math.abs(seatDiff)} seat{Math.abs(seatDiff) !== 1 ? 's' : ''}
              </p>
              <p className="text-sm text-green-700 dark:text-green-300">
                Credit will be applied to your next invoice
              </p>
            </>
          )}
        </div>
      )}

      {/* Action buttons */}
      {seatDiff !== 0 && (
        <div className="flex gap-3">
          <button
            onClick={() => setPendingSeats(currentSeats)}
            disabled={isUpdating}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={() => setShowConfirm(true)}
            disabled={isUpdating}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {isUpdating ? 'Updating...' : 'Update Seats'}
          </button>
        </div>
      )}

      {/* Confirmation modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowConfirm(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Confirm Seat Change
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {seatDiff > 0
                ? `You'll be charged ~$${formatPrice(estimatedProration)} today for ${seatDiff} additional seat${seatDiff !== 1 ? 's' : ''}.`
                : `You'll receive a credit for ${Math.abs(seatDiff)} seat${Math.abs(seatDiff) !== 1 ? 's' : ''} on your next invoice.`}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateSeats}
                disabled={isUpdating}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {isUpdating ? 'Processing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
