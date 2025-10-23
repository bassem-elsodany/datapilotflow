import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import { Stack } from '@mantine/core';
import { JobStatisticsCharts } from './job-statistics-charts';
import { RealTimeJobTableImproved } from './real-time-job-table-improved';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Knowledge', href: paths.dashboard.management.knowledge.root },
  { label: 'Job Status' },
];

export default function KnowledgeStatusPage() {
  return (
    <Page title="Job Status">
      <PageHeader title="Job Status" breadcrumbs={breadcrumbs} />

      <Stack gap="lg">
        {/* Job statistics charts */}
        <JobStatisticsCharts />

        {/* Real-time job table - NEW: Improved with modern UI and fixed cancel button */}
        <RealTimeJobTableImproved />
      </Stack>
    </Page>
  );
}
