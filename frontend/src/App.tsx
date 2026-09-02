import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { DashboardOverview } from './pages/DashboardOverview';
import { OpportunitiesPage } from './pages/OpportunitiesPage';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const handleSelectOpportunity = (eventId: string) => {
    setSelectedEventId(eventId);
    setCurrentTab('opportunity_detail');
  };

  const handleBackToOpportunities = () => {
    setSelectedEventId(null);
    setCurrentTab('opportunities');
  };

  return (
    <Layout currentTab={currentTab} setCurrentTab={setCurrentTab}>
      {currentTab === 'overview' && (
        <DashboardOverview
          onSelectOpportunity={handleSelectOpportunity}
          onNavigateToOpportunities={() => setCurrentTab('opportunities')}
        />
      )}

      {currentTab === 'opportunities' && (
        <OpportunitiesPage onSelectOpportunity={handleSelectOpportunity} />
      )}

      {currentTab === 'opportunity_detail' && selectedEventId && (
        <OpportunityDetailPage
          eventId={selectedEventId}
          onBack={handleBackToOpportunities}
        />
      )}

      {currentTab === 'analytics' && <AnalyticsPage />}

      {currentTab === 'audit' && <AuditTrailPage />}

      {currentTab === 'settings' && <SettingsPage />}
    </Layout>
  );
};

export default App;
