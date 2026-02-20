'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useState } from 'react';

export default function ProfileSettingsPage() {
  const [formData, setFormData] = useState({
    fullName: 'Sarah Anderson',
    email: 'sarah@example.com',
    company: 'Trend Analytics Inc',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Profile Card */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>
            Update your profile details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar */}
          <div className="flex items-center gap-4">
            <Avatar className="h-20 w-20">
              <AvatarImage src="https://i.pravatar.cc/80?u=sarah" alt="Sarah" />
              <AvatarFallback>SA</AvatarFallback>
            </Avatar>
            <Button variant="outline">Change Avatar</Button>
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Full Name</label>
              <Input
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className="mt-2"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Email Address</label>
              <Input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="mt-2"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Company</label>
              <Input
                name="company"
                value={formData.company}
                onChange={handleChange}
                className="mt-2"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button>Save Changes</Button>
            <Button variant="outline">Cancel</Button>
          </div>
        </CardContent>
      </Card>

      {/* Password Card */}
      <Card>
        <CardHeader>
          <CardTitle>Password</CardTitle>
          <CardDescription>
            Change your password
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Current Password</label>
            <Input type="password" className="mt-2" />
          </div>
          <div>
            <label className="text-sm font-medium">New Password</label>
            <Input type="password" className="mt-2" />
          </div>
          <div>
            <label className="text-sm font-medium">Confirm Password</label>
            <Input type="password" className="mt-2" />
          </div>
          <Button>Update Password</Button>
        </CardContent>
      </Card>
    </div>
  );
}
