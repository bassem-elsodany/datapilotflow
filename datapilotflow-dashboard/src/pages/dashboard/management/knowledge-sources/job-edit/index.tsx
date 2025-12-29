import { useParams } from 'react-router-dom';
import KnowledgeJobFormPage from '../job-create';

export default function KnowledgeJobEditPage() {
  const { jobId } = useParams<{ jobId: string }>();

  if (!jobId) {
    return <div>Job ID is required</div>;
  }

  return <KnowledgeJobFormPage jobId={jobId} />;
}