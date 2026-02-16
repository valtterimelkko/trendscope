import Link from 'next/link';

interface LogoProps {
  className?: string;
  showText?: boolean;
}

export function Logo({ className = '', showText = true }: LogoProps) {
  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <div className="w-8 h-8 bg-(--color-primary) rounded-md flex items-center justify-center">
        <span className="text-white font-bold text-xl">T</span>
      </div>
      {showText && (
        <span className="text-xl font-bold text-(--color-foreground)">
          Trendscope
        </span>
      )}
    </Link>
  );
}
