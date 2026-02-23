import Image from 'next/image';
import Link from 'next/link';

interface LogoProps {
  className?: string;
  width?: number;
  height?: number;
  showText?: boolean;
  textClassName?: string;
  variant?: 'white' | 'black';
}

export function Logo({ 
  className = '', 
  width = 32, 
  height = 32,
  showText = true,
  textClassName = "text-xl font-bold",
  variant = 'white'
}: LogoProps) {
  const logoSrc = variant === 'black' ? '/images/logo-black.png' : '/images/logo.png';
  const textColor = variant === 'black' ? 'text-black' : 'text-white';

  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <div className="relative flex items-center justify-center shrink-0">
        <Image
          src={logoSrc}
          alt="Trendscope Logo"
          width={width}
          height={height}
          priority
          className="object-contain"
        />
      </div>
      {showText && (
        <span className={`${textClassName} ${textColor}`}>Trendscope</span>
      )}
    </Link>
  );
}
