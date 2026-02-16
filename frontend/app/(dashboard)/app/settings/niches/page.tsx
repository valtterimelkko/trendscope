'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { X, Search } from 'lucide-react';
import { useState } from 'react';

const AVAILABLE_NICHES = [
  'beauty', 'fashion', 'finance', 'gaming', 'comedy', 'lifestyle',
  'food', 'fitness', 'travel', 'education', 'business', 'entertainment',
  'sports', 'music', 'art', 'tech', 'health', 'pets', 'diy', 'motivation',
];

export default function NichesSettingsPage() {
  const [selectedNiches, setSelectedNiches] = useState(['beauty', 'fashion', 'finance']);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredNiches = AVAILABLE_NICHES.filter((niche) =>
    niche.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleNiche = (niche: string) => {
    setSelectedNiches((prev) =>
      prev.includes(niche) ? prev.filter((n) => n !== niche) : [...prev, niche]
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Selected Niches</CardTitle>
          <CardDescription>
            You&apos;re monitoring {selectedNiches.length} niche{selectedNiches.length !== 1 && 's'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {selectedNiches.length === 0 ? (
              <p className="text-sm text-muted-foreground">No niches selected</p>
            ) : (
              selectedNiches.map((niche) => (
                <Badge key={niche} variant="secondary" className="px-3 py-1.5">
                  #{niche}
                  <button
                    onClick={() => toggleNiche(niche)}
                    className="ml-2 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add Niches</CardTitle>
          <CardDescription>
            Select niches to monitor for emerging trends
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search niches..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {filteredNiches.map((niche) => (
              <Button
                key={niche}
                variant={selectedNiches.includes(niche) ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleNiche(niche)}
              >
                #{niche}
              </Button>
            ))}
          </div>

          <div className="flex justify-end pt-4">
            <Button>Save Changes</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
