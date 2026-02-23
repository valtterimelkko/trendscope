import Image from 'next/image';
import Link from 'next/link';

interface LogoProps {
  className?: string;
  width?: number;
  height?: number;
  showText?: boolean;
  textClassName?: string;
}

export function Logo({ 
  className = '', 
  width = 32, 
  height = 32,
  showText = true,
  textClassName = "text-xl font-bold"
}: LogoProps) {
  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <div className="relative flex items-center justify-center shrink-0">
        <Image
          src="/images/logo.png"
          alt="Trendscope Logo"
          width={width}
          height={height}
          priority
          className="object-contain"
        />
      </div>
      {showText && (
        <span className={`${textClassName} text-foreground`}>Trendscope</span>
      )}
    </Link>
  );
}
