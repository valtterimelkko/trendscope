import { Logo } from '@/components/common/Logo';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mail } from 'lucide-react';

export default function VerifyEmailPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          <div className="flex justify-center mb-6">
            <Logo variant="black" width={260} height={72} showText={false} />
          </div>
          <div className="flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <Mail className="h-8 w-8 text-primary" />
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl">Check your email</CardTitle>
            <CardDescription className="mt-2">
              We&apos;ve sent a verification link to your email address.
              Click the link to activate your account.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Didn&apos;t receive the email? Check your spam folder.
          </p>
          <Button variant="outline" className="w-full">
            Resend verification email
          </Button>
          <Button variant="ghost" className="w-full" asChild>
            <a href="/auth/login">Back to login</a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
