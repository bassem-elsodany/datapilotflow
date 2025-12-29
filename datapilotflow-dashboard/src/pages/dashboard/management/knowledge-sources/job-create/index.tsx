import { useCreateDocumentSplitter, useUpdateDocumentSplitter } from '@/api/resources/document-splitters';
import { useCreateKnowledgeJob, useGetKnowledgeJob, useUpdateKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { useGetModelProviders } from '@/api/resources/model-providers';
import { useGetKnowledgeVectorDBCollections } from '@/api/resources/vectordb-collections';
import { ColorfulVerticalStepper, StepConfig } from '@/components/colorful-vertical-stepper';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiEndpoints, app } from '@/config';
import {
  ActionIcon,
  Alert,
  Box,
  Button,
  Center,
  Divider,
  Group,
  Loader,
  NumberInput,
  Paper,
  Radio,
  Select,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  TextInput,
  Textarea,
  Tooltip
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconArrowLeft,
  IconBrain,
  IconClipboardCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconInfoCircle,
  IconScissors,
  IconWand
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface KnowledgeJobFormProps {
  jobId?: string; // Optional jobId for edit mode
}

export default function KnowledgeJobFormPage({ jobId }: KnowledgeJobFormProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [isExplicitSubmit, setIsExplicitSubmit] = useState(false);
  const [useExistingCollection, setUseExistingCollection] = useState(false);
  const [formPopulated, setFormPopulated] = useState(false);
  const [splitterId, setSplitterId] = useState<string | null>(null);
  const [isCreatingSplitter, setIsCreatingSplitter] = useState(false);

  const isEditMode = !!jobId;

  // Get configId from navigation state (passed from configs page)
  const locationState = location.state as { configId?: string; configName?: string } | null;

  // API hooks
  const { data: configs, isLoading: configsLoading } = useGetKnowledgeSourceConfigs();
  const { data: modelProviders, isLoading: providersLoading } = useGetModelProviders();
  const { data: vectordbCollections } = useGetKnowledgeVectorDBCollections();

  // Edit mode hooks - use expanded job data with all related data
  // Only fetch job data when in edit mode with a valid jobId
  // The hook will automatically prevent any requests when enabled=false
  const { data: job, isLoading: jobLoading, error: jobError } = useGetKnowledgeJob(
    jobId, // Pass jobId directly - the hook handles undefined values safely
    {
      enabled: isEditMode && !!jobId, // Only fetch when we have a valid jobId in edit mode
      query: { expand: 'document_splitter,vectordb_collection,knowledge_source_config' },
    }
  );

  // Debug logging
  useEffect(() => {
    console.log('Component mounted/updated:', {
      isEditMode,
      jobId,
      job,
      jobLoading
    });
  }, [isEditMode, jobId, job, jobLoading]);

  // Mutations
  const createJobMutation = useCreateKnowledgeJob();
  const updateJobMutation = useUpdateKnowledgeJob();
  const createSplitterMutation = useCreateDocumentSplitter();
  const updateSplitterMutation = useUpdateDocumentSplitter();

  // Form setup
  const form = useForm({
    initialValues: {
      config_id: '',
      name: '',
      description: '',
      // Vector DB Collection Configuration
      use_existing_collection: false,
      existing_collection_id: '',
      vectordb_collection_description: '',
      embedding_model_provider_id: '',
      embedding_model_name: '',
      vector_dimension: 1536,
      collection_name: '',

      // Document Splitting Configuration
      splitter_type: 'text',
      chunk_size: 256,
      chunk_overlap: 32,
      headers_to_split_on: [['#', 'Header 1'], ['##', 'Header 2'], ['###', 'Header 3']],
      sections_to_split_on: [['h1', 'Header 1'], ['h2', 'Header 2'], ['h3', 'Header 3']],
      // Job processing configuration
      batch_size: 20,
      save_to_file: false,
      write_consolidated_file: false,

      // Collection management
      clear_collection_before_start: false,
      check_duplicates_before_insert: false
    },
    validate: {
      config_id: (value) => (!value ? 'Configuration is required' : null),
      name: (value) => (!value ? 'Job name is required' : null),
      existing_collection_id: (value, values) => (values.use_existing_collection && !value ? 'Existing collection is required' : null),
      embedding_model_provider_id: (value, values) => (!values.use_existing_collection && !value ? 'Embedding model provider is required' : null),
      embedding_model_name: (value, values) => (!values.use_existing_collection && !value ? 'Embedding model is required' : null),
      vector_dimension: (value, values) => (!values.use_existing_collection && (value < 1 || value > 4096) ? 'Vector dimension must be between 1 and 4096' : null),
      collection_name: (value, values) => (!values.use_existing_collection && !value ? 'Collection name is required' : null),
      batch_size: (value) => (value < 1 || value > 1000 ? 'Batch size must be between 1 and 1000' : null),
    },
  });

  // Helper functions
  const getConfigName = (configId: string) => {
    const config = configs?.find(c => c.id === configId);
    return config ? config.name : 'Unknown Configuration';
  };

  const getProviderName = (providerId: string) => {
    const provider = modelProviders?.find(p => p.id === providerId);
    return provider ? provider.name : 'Unknown Provider';
  };

  // Get selected configuration details
  const selectedConfig = configs?.find(c => c.id === form.values.config_id);

  // Determine recommended splitter based on output format
  const getRecommendedSplitter = () => {
    if (!selectedConfig) return null;

    switch (selectedConfig.output_format) {
      case 'markdown':
      case 'llm_markdown':
        return {
          type: 'document',
          reason: 'Your source configuration outputs markdown format, which is ideal for document-structured splitting that preserves content hierarchy.',
          icon: 'document'
        };
      case 'html':
        return {
          type: 'text',
          reason: 'Your source configuration outputs HTML format, which works best with text-based splitting for consistent chunking.',
          icon: 'text'
        };
      default:
        return null;
    }
  };

  const recommendedSplitter = getRecommendedSplitter();

  const embeddingProviders = useMemo(() => {
    return modelProviders?.filter(provider => provider.embedding) || [];
  }, [modelProviders]);

  const embeddingModels = useMemo(() => {
    const provider = modelProviders?.find(p => p.id === form.values.embedding_model_provider_id);
    return provider?.embedding?.models || [];
  }, [modelProviders, form.values.embedding_model_provider_id]);

  // Calculate recommended chunk size and overlap based on embedding model's max token limit
  const embeddingMaxTokens = useMemo(() => {
    const provider = modelProviders?.find(p => p.id === form.values.embedding_model_provider_id);
    if (!provider?.embedding?.config) return null;

    const maxInputTokens = provider.embedding.config.max_input_tokens;
    if (!maxInputTokens) return null;

    // Parse max_input_tokens (could be string or number)
    const maxTokens = typeof maxInputTokens === 'string' ? parseInt(maxInputTokens) : maxInputTokens;
    if (isNaN(maxTokens) || maxTokens <= 0) return null;

    return maxTokens;
  }, [modelProviders, form.values.embedding_model_provider_id]);

  const recommendedChunkConfig = useMemo(() => {
    if (!embeddingMaxTokens) {
      // Default values if no max token limit is available
      return { chunkSize: 256, chunkOverlap: 32, maxAllowed: 4096 };
    }

    // Allow up to 95% of max tokens (5% safety buffer)
    const maxAllowedTotal = Math.floor(embeddingMaxTokens * 0.95);

    // Split the 95% between chunk (82.5%) and overlap (12.5%)
    // This ensures chunk + overlap = 95% of max tokens
    const optimalChunkSize = Math.floor(embeddingMaxTokens * 0.825);  // 82.5%
    const optimalOverlap = Math.floor(embeddingMaxTokens * 0.125);    // 12.5%

    // Verify total doesn't exceed 95% limit
    const totalTokens = optimalChunkSize + optimalOverlap;
    let finalChunkSize = optimalChunkSize;
    let finalOverlap = optimalOverlap;

    if (totalTokens > maxAllowedTotal) {
      // Adjust proportionally to fit within 95% limit
      const ratio = maxAllowedTotal / totalTokens;
      finalChunkSize = Math.floor(optimalChunkSize * ratio);
      finalOverlap = Math.floor(optimalOverlap * ratio);
    }

    // Ensure values are within reasonable bounds
    finalChunkSize = Math.max(64, Math.min(finalChunkSize, embeddingMaxTokens));
    finalOverlap = Math.max(0, Math.min(finalOverlap, Math.floor(finalChunkSize / 2)));

    return {
      chunkSize: finalChunkSize,
      chunkOverlap: finalOverlap,
      maxTokens: embeddingMaxTokens,
      maxAllowed: maxAllowedTotal
    };
  }, [embeddingMaxTokens]);

  // Step configurations with brand colors
  const stepConfigs: StepConfig[] = [
    {
      label: 'Job Setup',
      description: 'Basic job information',
      icon: <IconClock size={20} strokeWidth={2} />,
      color: '#45c9bb',
      gradientFrom: '#45c9bb',
      gradientTo: '#87cbbc'
    },
    {
      label: 'Vector DB Collection',
      description: 'Configure vector database',
      icon: <IconDatabase size={20} strokeWidth={2} />,
      color: '#bbe773',
      gradientFrom: '#bbe773',
      gradientTo: '#9dd245'
    },
    {
      label: 'Embedding Model',
      description: form.values.use_existing_collection ? 'Skip - Using existing' : 'Select embedding model',
      icon: <IconBrain size={20} strokeWidth={2} />,
      color: '#3bc57d',
      gradientFrom: '#3bc57d',
      gradientTo: '#45c9bb'
    },
    {
      label: 'Document Splitter',
      description: 'Choose splitting strategy',
      icon: <IconScissors size={20} strokeWidth={2} />,
      color: '#ddde65',
      gradientFrom: '#ddde65',
      gradientTo: '#bbe773'
    },
    {
      label: 'Processing',
      description: 'Job processing settings',
      icon: <IconCpu size={20} strokeWidth={2} />,
      color: '#ae89ae',
      gradientFrom: '#ae89ae',
      gradientTo: '#87cbbc'
    },
    {
      label: isEditMode ? 'Review & Update' : 'Review & Create',
      description: isEditMode ? 'Review and update job' : 'Review and create job',
      icon: <IconClipboardCheck size={20} strokeWidth={2} />,
      color: '#45c9bb',
      gradientFrom: '#45c9bb',
      gradientTo: '#3bc57d'
    }
  ];

  // Load job data for edit mode
  useEffect(() => {
    if (isEditMode && job && job.vectordb_collection && job.document_splitter && !formPopulated) {
      console.log('Loading job data for edit:', job);
      console.log('Vector DB collection:', job.vectordb_collection);
      console.log('Document splitter:', job.document_splitter);

      const formValues = {
        config_id: job.knowledge_source_config_id,
        name: job.name,
        description: job.description || '',
        // Vector DB Collection Configuration from expanded data
        vectordb_collection_description: job.vectordb_collection.description,
        embedding_model_provider_id: job.vectordb_collection.embedding_model_provider_id,
        embedding_model_name: job.vectordb_collection.embedding_model_name,
        vector_dimension: job.vectordb_collection.vector_dimension,
        collection_name: job.vectordb_collection.collection_name,
        // Document splitting configuration from expanded splitter data
        splitter_type: job.document_splitter.splitter_type,
        chunk_size: job.document_splitter.chunk_size ?? 256,
        chunk_overlap: job.document_splitter.chunk_overlap ?? 32,
        headers_to_split_on: job.document_splitter.headers_to_split_on || [],
        // Job processing configuration
        batch_size: job.batch_size,
        save_to_file: job.save_to_file ?? false,
        write_consolidated_file: job.write_consolidated_file ?? false,
        // Collection management
        clear_collection_before_start: job.clear_collection_before_start ?? false,
        check_duplicates_before_insert: job.check_duplicates_before_insert ?? false,
        // Vector DB Collection mode
        use_existing_collection: true, // In edit mode, we're always using existing
        existing_collection_id: job.vectordb_collection_id || ''
      };

      console.log('Setting form values for edit:', formValues);
      form.setValues(formValues);
      setSplitterId(job.splitter_id || null);
      setUseExistingCollection(true);
      setFormPopulated(true);
    }
  }, [isEditMode, job, formPopulated]);

  // Debug form values
  useEffect(() => {
    if (isEditMode) {
      console.log('Form values in edit mode:', form.values);
    }
  }, [form.values, isEditMode]);

  // Pre-select config from navigation state (create mode only)
  useEffect(() => {
    if (!isEditMode && locationState?.configId && configs && configs.length > 0) {
      // Check if the config exists in the loaded configs
      const selectedConfig = configs.find(c => c.id === locationState.configId);
      if (selectedConfig && !form.values.config_id) {
        console.log('Pre-selecting config from navigation state:', locationState.configId);
        form.setFieldValue('config_id', locationState.configId);
        
        // Also populate job name with default: "{Config Name} Job"
        if (!form.values.name) {
          const defaultJobName = `${selectedConfig.name} Job`;
          console.log('Setting default job name:', defaultJobName);
          form.setFieldValue('name', defaultJobName);
        }
        
        // Populate description with config description or default message
        if (!form.values.description) {
          const defaultDescription = selectedConfig.description 
            ? `Processing job for ${selectedConfig.name}: ${selectedConfig.description}`
            : `Processing job for ${selectedConfig.name}`;
          console.log('Setting default job description:', defaultDescription);
          form.setFieldValue('description', defaultDescription);
        }
      }
    }
  }, [isEditMode, locationState, configs, form]);

  // Helper function to render inactive provider warning
  const renderInactiveProviderWarning = () => {
    if (!form.values.embedding_model_provider_id) return null;
    const selectedProvider = embeddingProviders.find(p => p.id === form.values.embedding_model_provider_id);
    if (selectedProvider && !selectedProvider.is_active) {
      return (
        <Alert
          icon={<IconAlertTriangle size={16} />}
          title="Inactive Provider"
          color="orange"
          variant="light"
        >
          This provider is inactive. Please enable it and set the API key in the Model Providers settings before creating a job.
        </Alert>
      );
    }
    return null;
  };

  // Ensure form is properly initialized
  useEffect(() => {
    // Clear any potential persisted state
    localStorage.removeItem('knowledge-job-form');
    sessionStorage.removeItem('knowledge-job-form');

    // Reset form to initial state when component mounts (only for create mode)
    if (!isEditMode) {
      form.reset();
      // Force clear the embedding model provider field
      form.setFieldValue('embedding_model_provider_id', '');
      form.setFieldValue('embedding_model_name', '');
      setFormPopulated(false);
      console.log('Form reset on mount (create mode):', form.values);
    } else {
      setFormPopulated(false); // Reset flag for edit mode
      console.log('Skipping form reset in edit mode');
    }
  }, [isEditMode]);

  // Debug form values
  useEffect(() => {
    console.log('Form values changed:', form.values);
  }, [form.values]);


  // Step validation
  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        // Job Setup - only basic job information
        return !!(form.values.config_id && form.values.name);
      case 1:
        // Vector DB Collection Configuration
        if (form.values.use_existing_collection) {
          return !!form.values.existing_collection_id;
        }
        return !!form.values.collection_name;
      case 2:
        // Embedding Model
        if (form.values.use_existing_collection) {
          return true; // Skip embedding validation for existing collections
        }
        const hasValidProvider = !!(form.values.embedding_model_provider_id && form.values.embedding_model_name && form.values.vector_dimension >= 1 && form.values.vector_dimension <= 4096);
        if (hasValidProvider) {
          const selectedProvider = embeddingProviders.find(p => p.id === form.values.embedding_model_provider_id);
          return selectedProvider ? selectedProvider.is_active : false;
        }
        return false;
      case 3:
        // Document Splitter
        if (form.values.splitter_type === 'text' || form.values.splitter_type === 'document') {
          const maxChunkSize = embeddingMaxTokens || 4096; // Use embedding model's max or default to 4096
          const maxOverlap = Math.floor(maxChunkSize / 2); // Max overlap is 50% of chunk size
          const maxTotal = Math.floor(maxChunkSize * 0.95); // Allow up to 95% of max tokens (5% buffer)

          // Check individual constraints
          if (form.values.chunk_size < 64) {
            notifications.show({
              title: 'Validation Error',
              message: 'Chunk size must be at least 64 tokens',
              color: 'red',
              autoClose: 4000,
            });
            return false;
          }

          if (form.values.chunk_size > maxChunkSize) {
            notifications.show({
              title: 'Validation Error',
              message: `Chunk size (${form.values.chunk_size}) exceeds embedding model's maximum of ${maxChunkSize} tokens`,
              color: 'red',
              autoClose: 4000,
            });
            return false;
          }

          if (form.values.chunk_overlap < 0) {
            notifications.show({
              title: 'Validation Error',
              message: 'Chunk overlap cannot be negative',
              color: 'red',
              autoClose: 4000,
            });
            return false;
          }

          if (form.values.chunk_overlap > maxOverlap) {
            notifications.show({
              title: 'Validation Error',
              message: `Chunk overlap (${form.values.chunk_overlap}) exceeds maximum of ${maxOverlap} tokens (50% of chunk size)`,
              color: 'red',
              autoClose: 4000,
            });
            return false;
          }

          const totalTokens = form.values.chunk_size + form.values.chunk_overlap;
          if (totalTokens > maxTotal) {
            notifications.show({
              title: 'Validation Error',
              message: `Total tokens (chunk ${form.values.chunk_size} + overlap ${form.values.chunk_overlap} = ${totalTokens}) exceeds 95% of model's max tokens (${maxTotal}). Please reduce chunk size or overlap.`,
              color: 'red',
              autoClose: 5000,
            });
            return false;
          }

          return true;
        }
        return true; // HTML splitting doesn't need chunking validation
      case 4:
        // Processing - batch size and output settings
        const hasValidBatchSize = form.values.batch_size >= 1 && form.values.batch_size <= 1000;
        return !!hasValidBatchSize;
      case 5:
        // Review & Create Job - always valid once we reach this step
        return true;
      default:
        return false;
    }
  };

  // Navigation functions
  const nextStep = async () => {
    console.log('nextStep called, current activeStep:', activeStep);

    // Special validation for step 1 - check collection name uniqueness
    if (activeStep === 1 && !form.values.use_existing_collection && form.values.collection_name) {
      try {
        // Make API call to check collection name
        const fullUrl = `${app.apiBaseUrl}${apiEndpoints.vectordb.checkName(form.values.collection_name)}`;
        console.log('Checking collection name at:', fullUrl);

        // Get the auth token from localStorage
        const token = localStorage.getItem('jwt_token');

        const response = await fetch(fullUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        });

        if (!response.ok) {
          let errorMessage = `Server error (${response.status})`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch {
            // If we can't parse the error response, use the status-based message
          }
          throw new Error(errorMessage);
        }

        const checkResult = await response.json();
        console.log('Collection name check result:', checkResult);

        if (checkResult.exists) {
          notifications.show({
            title: 'Collection Name Already Exists',
            message: `The collection name '${form.values.collection_name}' is already in use. Please choose a different name.`,
            color: 'red',
          });
          return;
        }
      } catch (error) {
        console.error('Error checking collection name:', error);

        let errorMessage = 'Unknown error occurred';
        if (error instanceof Error) {
          if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
          } else if (error.message.includes('Server error')) {
            errorMessage = `Server error: ${error.message}`;
          } else {
            errorMessage = error.message;
          }
        }

        notifications.show({
          title: 'Collection Name Validation Failed',
          message: errorMessage,
          color: 'red',
        });
        return;
      }
    }

    if (validateStep(activeStep)) {
      console.log('Step validation passed, moving to step:', activeStep + 1);
      setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
      setActiveStep(activeStep + 1);
      setIsExplicitSubmit(false); // Reset explicit submit flag when moving to next step
    } else {
      console.log('Step validation failed for step:', activeStep);
      let errorMessage = 'Please complete the current step before proceeding.';

      // Show specific error for inactive provider
      if (activeStep === 1 && form.values.embedding_model_provider_id) {
        const selectedProvider = embeddingProviders.find(p => p.id === form.values.embedding_model_provider_id);
        if (selectedProvider && !selectedProvider.is_active) {
          errorMessage = 'Please select an active embedding model provider. Enable the provider and set the API key in Model Providers settings.';
        }
      }


      notifications.show({
        title: 'Validation Error',
        message: errorMessage,
        color: 'red',
      });
    }
  };

  const prevStep = () => {
    setActiveStep(activeStep - 1);
    setIsExplicitSubmit(false); // Reset explicit submit flag when going back
  };

  const handleStepClick = (step: number) => {
    // Allow going back to previous steps
    if (step < activeStep) {
      setActiveStep(step);
      return;
    }

    // Allow going to next step only if current step is completed
    if (step === activeStep + 1) {
      if (validateStep(activeStep)) {
        setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
        setActiveStep(step);
      } else {
        notifications.show({
          title: 'Validation Error',
          message: 'Please complete the current step before proceeding.',
          color: 'red',
        });
      }
      return;
    }

    // Allow going to any completed step
    if (completedSteps.includes(step)) {
      setActiveStep(step);
      return;
    }

    // Block navigation to future steps
    notifications.show({
      title: 'Navigation Blocked',
      message: 'Please complete the previous steps before proceeding.',
      color: 'orange',
    });
  };

  // Handle document splitter creation/update
  const handleSplitterConfig = async (values: typeof form.values): Promise<string> => {
    const splitterData = {
      name: `${values.name} - Splitter`,
      description: `Document splitter for job: ${values.name}`,
      splitter_type: values.splitter_type as 'text' | 'document' | 'html', // Cast to expected type
      chunk_size: values.chunk_size,
      chunk_overlap: values.chunk_overlap,
      headers_to_split_on: values.headers_to_split_on as [string, string][], // Cast to tuple array
    };

    if (isEditMode && splitterId) {
      // Update existing splitter configuration
      console.log('Updating existing splitter:', splitterId, splitterData);
      return new Promise((resolve, reject) => {
        updateSplitterMutation.mutate(
          {
            variables: splitterData as any, // Use 'as any' to bypass type checking for mutation
            route: { splitterId }
          },
          {
            onSuccess: (data) => {
              console.log('Splitter updated successfully:', data);
              resolve(data.id);
            },
            onError: (error) => {
              console.error('Splitter update error:', error);
              reject(error);
            }
          }
        );
      });
    } else {
      // Create new splitter configuration
      console.log('Creating new splitter:', splitterData);
      return new Promise((resolve, reject) => {
        createSplitterMutation.mutate(
          {
            variables: splitterData as any // Use 'as any' to bypass type checking for mutation
          },
          {
            onSuccess: (data) => {
              console.log('Splitter created successfully:', data);
              resolve(data.id);
            },
            onError: (error) => {
              console.error('Splitter creation error:', error);
              reject(error);
            }
          }
        );
      });
    }
  };

  const handleSubmitJob = async (values: typeof form.values) => {
    try {
      setIsCreatingSplitter(true);

      // Create or update document splitter configuration
      const newSplitterId = await handleSplitterConfig(values);
      setSplitterId(newSplitterId);
      const jobData = {
        name: values.name,
        description: values.description,
        // Use splitter_id instead of raw splitter fields
        splitter_id: newSplitterId,
        // Job processing configuration
        batch_size: values.batch_size,
        save_to_file: values.save_to_file ?? false,
        write_consolidated_file: values.write_consolidated_file ?? false,

        // Collection management
        clear_collection_before_start: values.clear_collection_before_start ?? false,
        check_duplicates_before_insert: values.check_duplicates_before_insert ?? false,
      };

      // Add collection configuration based on user choice
      if (values.use_existing_collection) {
        // Use existing collection
        Object.assign(jobData, {
          existing_collection_id: values.existing_collection_id,
        });
      } else {
        // Create new collection
        Object.assign(jobData, {
          vectordb_collection_description: values.vectordb_collection_description,
          embedding_model_provider_id: values.embedding_model_provider_id,
          embedding_model_name: values.embedding_model_name,
          vector_dimension: values.vector_dimension,
          collection_name: values.collection_name,
        });
      }

      if (isEditMode && jobId) {
        // Update existing job - filter out fields not allowed in updates
        const updateData = { ...jobData };
        delete (updateData as any).existing_collection_id; // Not allowed in updates
        delete (updateData as any).config_id; // Not allowed in updates

        // In edit mode, we only update the splitter_id reference, not the splitter config itself
        // The splitter configuration is updated separately above
        console.log('Sending job update data:', updateData);

        updateJobMutation.mutate(
          {
            variables: updateData as any,
            route: { jobId }
          },
          {
            onSuccess: () => {
              notifications.show({
                title: 'Success',
                message: 'Knowledge injection job updated successfully!',
                color: 'green',
              });
              navigate('/dashboard/management/knowledge-sources/jobs');
            },
            onError: (error: any) => {
              console.error('Update job error:', error);
              notifications.show({
                title: 'Error',
                message: error.message || 'Failed to update knowledge injection job',
                color: 'red',
              });
            },
          }
        );
      } else {
        // Create new job
        createJobMutation.mutate(
          {
            variables: jobData as any,
            route: { configId: values.config_id }
          },
          {
            onSuccess: () => {
              notifications.show({
                title: 'Success',
                message: 'Knowledge injection job created successfully!',
                color: 'green',
              });
              navigate('/dashboard/management/knowledge-sources/jobs');
            },
            onError: (error: any) => {
              notifications.show({
                title: 'Error',
                message: error.message || 'Failed to create knowledge injection job',
                color: 'red',
              });
            },
          }
        );
      }
    } catch (error: any) {
      console.error('Splitter creation error:', error);
      notifications.show({
        title: 'Error',
        message: error.message || 'Failed to create document splitter configuration',
        color: 'red',
      });
    } finally {
      setIsCreatingSplitter(false);
    }
  };

  const handleCancel = () => {
    navigate('/dashboard/management/knowledge-sources/jobs');
  };

  // Show loading for edit mode
  if (isEditMode && jobLoading) {
    return (
      <Page title="Edit Knowledge Injection Job">
        <Center h={400}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  // Show error for edit mode
  if (isEditMode && jobError) {
    return (
      <Page title="Edit Knowledge Injection Job">
        <Center h={400}>
          <Stack align="center" gap="md">
            <Text color="red" size="lg">Failed to load job data</Text>
            <Text color="dimmed">Error: {jobError.message || 'Unknown error'}</Text>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </Stack>
        </Center>
      </Page>
    );
  }

  if (configsLoading || providersLoading) {
    return (
      <Page title={isEditMode ? "Edit Knowledge Injection Job" : "Create Knowledge Injection Job"}>
        <Center h={400}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  // Show error if job is not found in edit mode
  if (isEditMode && !jobLoading && !job) {
    return (
      <Page title="Edit Knowledge Injection Job">
        <Center h={400}>
          <Stack align="center" gap="md">
            <Text color="red" size="lg">Job not found</Text>
            <Text color="dimmed">The job you're trying to edit does not exist or you don't have permission to access it.</Text>
            <Button onClick={() => navigate('/dashboard/management/knowledge-sources/jobs')}>Back to Jobs</Button>
          </Stack>
        </Center>
      </Page>
    );
  }

  return (
    <Page title={isEditMode ? "Edit Knowledge Injection Job" : "Create Knowledge Injection Job"}>
      <PageHeader
        title={isEditMode ? "Edit Knowledge Injection Job" : "Create Knowledge Injection Job"}
        breadcrumbs={[
          { label: 'Knowledge Sources', href: '/dashboard/management/knowledge-sources' },
          { label: 'Jobs', href: '/dashboard/management/knowledge-sources/jobs' },
          { label: isEditMode ? 'Edit Job' : 'Create Job' },
        ]}
      />

      <Group justify="flex-end" mb="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          onClick={handleCancel}
        >
          Back to Jobs
        </Button>
      </Group>

      <Paper withBorder shadow="sm" p="lg" radius="md" mt="md">
        <form
          onSubmit={(e) => {
            console.log('Form submit triggered, activeStep:', activeStep, 'isExplicitSubmit:', isExplicitSubmit);
            // Only allow form submission on the final step (step 5 - Review & Create Job) AND when explicitly submitted
            if (activeStep !== 5 || !isExplicitSubmit) {
              console.log('Preventing form submission - activeStep:', activeStep, 'isExplicitSubmit:', isExplicitSubmit);
              e.preventDefault();
              e.stopPropagation();
              return false;
            }
            console.log('Allowing form submission on final step (Review & Create Job) with explicit submit');
            form.onSubmit(handleSubmitJob)(e);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              console.log('Enter key pressed on step:', activeStep);
              // Prevent accidental submit on Enter except on final step
              const isFinalStep = activeStep === 5; // steps: 0 setup, 1 vectordb, 2 splitter, 3 embedding, 4 processing, 5 review -> final action handled by button
              if (!isFinalStep) {
                console.log('Preventing Enter key submission on step:', activeStep);
                e.preventDefault();
                e.stopPropagation();
                return false;
              }
            }
          }}
        >
          <ColorfulVerticalStepper
            activeStep={activeStep}
            completedSteps={completedSteps}
            steps={stepConfigs}
            onStepClick={handleStepClick}
          >
            {activeStep === 0 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  <Text size="sm">
                    <strong>Step 1: Job Setup</strong><br />
                    Configure the basic information for your knowledge processing job. Select the knowledge source configuration that defines what content to process, and provide a descriptive name and description for this job.
                  </Text>
                </Alert>

                <Select
                  label="Knowledge Source Configuration"
                  placeholder="Select a configuration"
                  data={configs?.map(config => ({
                    value: config.id,
                    label: config.name
                  })) || []}
                  required
                  {...form.getInputProps('config_id')}
                />

                <TextInput
                  label="Job Name"
                  placeholder="Enter job name"
                  required
                  {...form.getInputProps('name')}
                />

                <Textarea
                  label="Job Description"
                  placeholder="Enter job description (optional)"
                  rows={3}
                  {...form.getInputProps('description')}
                />

              </Stack>
            )}

            {activeStep === 1 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  <Text size="sm">
                    <strong>Step 2: Vector DB Collection Configuration</strong><br />
                    Choose how to handle your vector database collection. You can either use an existing collection to append new data, or create a new collection with custom settings.
                  </Text>
                </Alert>

                <Box>
                  <Text fw={500} size="sm" mb="sm">Vector DB Collection Configuration</Text>
                  <Radio.Group
                    value={form.values.use_existing_collection ? 'existing' : 'new'}
                    onChange={(value) => {
                      form.setFieldValue('use_existing_collection', value === 'existing');
                    }}
                  >
                    <Stack gap="sm">
                      <Radio value="new" label="Create new Vector DB Collection" />
                      <Radio value="existing" label="Use existing Vector DB Collection" />
                    </Stack>
                  </Radio.Group>
                </Box>

                {form.values.use_existing_collection ? (
                  <>
                    <Select
                      label="Select Existing Vector DB Collection"
                      placeholder="Choose a collection to append to"
                      required
                      data={vectordbCollections?.map(collection => ({
                        value: collection.id,
                        label: `${collection.collection_name} (${collection.embedding_model_name})`
                      })) || []}
                      value={form.values.existing_collection_id}
                      onChange={(value) => {
                        form.setFieldValue('existing_collection_id', value || '');

                        // Auto-populate embedding model fields from selected collection
                        if (value) {
                          const selectedCollection = vectordbCollections?.find(c => c.id === value);
                          if (selectedCollection) {
                            form.setFieldValue('embedding_model_provider_id', selectedCollection.embedding_model_provider_id);
                            form.setFieldValue('embedding_model_name', selectedCollection.embedding_model_name);
                            form.setFieldValue('vector_dimension', selectedCollection.vector_dimension);
                            form.setFieldValue('collection_name', selectedCollection.collection_name);
                          }
                        }
                      }}
                    />

                    {/* Show inherited collection settings */}
                    {(() => {
                      const selectedCollection = vectordbCollections?.find(c => c.id === form.values.existing_collection_id);
                      if (!selectedCollection) return null;

                      return (
                        <Stack gap="md" mt="md">
                          <Text fw={500} size="sm">Inherited Collection Settings</Text>

                          {/* Collection Details */}
                          <Stack gap="sm">
                            <TextInput
                              label="Collection Name"
                              value={selectedCollection.collection_name}
                              disabled
                              description="Inherited from existing collection"
                            />

                            {selectedCollection.description && (
                              <Textarea
                                label="Collection Description"
                                value={selectedCollection.description}
                                disabled
                                description="Inherited from existing collection"
                                rows={2}
                              />
                            )}
                          </Stack>


                          {/* Embedding Model Settings */}
                          <Stack gap="sm">
                            <TextInput
                              label="Embedding Model Provider"
                              value={getProviderName(selectedCollection.embedding_model_provider_id)}
                              disabled
                              description="Inherited from existing collection"
                            />

                            <TextInput
                              label="Embedding Model"
                              value={selectedCollection.embedding_model_name}
                              disabled
                              description="Inherited from existing collection"
                            />

                            <NumberInput
                              label="Vector Dimension"
                              value={selectedCollection.vector_dimension}
                              disabled
                              description="Inherited from existing collection"
                            />
                          </Stack>
                        </Stack>
                      );
                    })()}
                  </>
                ) : (
                  <>
                    <TextInput
                      label="Collection Name"
                      placeholder="Enter the collection name for the vector database (only letters, numbers, and underscores allowed)"
                      required
                      description="This is the name of the collection that will be created in your vector database"
                      {...form.getInputProps('collection_name')}
                      onChange={(e) => {
                        const value = e.target.value.replace(/[^a-zA-Z0-9_]/g, '');
                        form.setFieldValue('collection_name', value);
                      }}
                    />

                    <Textarea
                      label="Collection Description"
                      placeholder="Enter a description for this collection configuration (optional)"
                      rows={2}
                      {...form.getInputProps('vectordb_collection_description')}
                    />

                  </>
                )}
              </Stack>
            )}

            {activeStep === 2 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  <Text size="sm">
                    <strong>Step 3: Embedding Model Configuration</strong><br />
                    {form.values.use_existing_collection
                      ? "Using an existing collection - embedding model settings are inherited from the selected collection."
                      : "Select the embedding model that will convert your documents into vector representations. Choose an active provider and model that best fits your content type and language."
                    }
                    <br /><br />
                    <strong>Vector Dimension Impact:</strong><br />
                    • <strong>Higher dimensions (1536-3072)</strong>: Better semantic understanding, more nuanced representations, but requires more storage and computational resources<br />
                    • <strong>Lower dimensions (384-768)</strong>: Faster processing, less storage, but may lose some semantic detail<br />
                    • <strong>Model-specific dimensions</strong>: Each embedding model has a fixed dimension (e.g., OpenAI text-embedding-ada-002 = 1536, text-embedding-3-large = 3072)<br />
                    • <strong>Consistency requirement</strong>: All documents in a collection must use the same dimension for proper similarity search
                  </Text>
                </Alert>

                {form.values.use_existing_collection ? (
                  <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                    Using existing Vector DB Collection. All embedding model and collection settings are inherited from the selected collection and shown in the previous step.
                  </Alert>
                ) : (
                  <>
                    <Select
                      key={`embedding-provider-${form.values.embedding_model_provider_id}`}
                      label="Embedding Model Provider"
                      placeholder="Select a provider"
                      data={embeddingProviders.map(provider => ({
                        value: provider.id,
                        label: `${provider.name} ${provider.is_active ? '(Active)' : '(Inactive)'}`
                      }))}
                      required
                      value={form.values.embedding_model_provider_id || ''}
                      onChange={(value) => {
                        console.log('Provider changed to:', value, 'Current activeStep:', activeStep);
                        if (value) {
                          form.setFieldValue('embedding_model_provider_id', value);
                          form.setFieldValue('embedding_model_name', ''); // Reset model selection

                          // Check if selected provider is inactive
                          const selectedProvider = embeddingProviders.find(p => p.id === value);
                          if (selectedProvider && !selectedProvider.is_active) {
                            notifications.show({
                              title: 'Inactive Provider Selected',
                              message: 'This provider is inactive. Please enable it and set the API key in the Model Providers settings.',
                              color: 'orange',
                              autoClose: 5000,
                            });
                          }
                        } else {
                          form.setFieldValue('embedding_model_provider_id', '');
                          form.setFieldValue('embedding_model_name', '');
                        }
                        console.log('After provider change, activeStep:', activeStep);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          e.stopPropagation();
                        }
                      }}
                    />

                    {/* Show warning for inactive provider */}
                    {renderInactiveProviderWarning()}

                    <Select
                      label="Embedding Model"
                      placeholder="Select a model"
                      data={embeddingModels.map(model => ({
                        value: model,
                        label: model
                      }))}
                      required
                      disabled={!form.values.embedding_model_provider_id}
                      {...form.getInputProps('embedding_model_name')}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          e.stopPropagation();
                        }
                      }}
                    />

                    <NumberInput
                      label="Vector Dimension"
                      placeholder="1536"
                      required
                      description="Dimension of the vector embeddings (1-4096). Common values: OpenAI text-embedding-ada-002 (1536), text-embedding-3-small (1536), text-embedding-3-large (3072)"
                      min={1}
                      max={4096}
                      {...form.getInputProps('vector_dimension')}
                    />
                  </>
                )}
              </Stack>
            )}

            {activeStep === 3 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  <Text size="sm">
                    <strong>Step 4: Document Splitting Strategy</strong><br />
                    Choose how to split your documents into chunks. You can use text-based splitting with configurable chunk size and overlap, or document-structured splitting that respects markdown headers.
                  </Text>
                </Alert>

                {/* Show recommendation based on source configuration */}
                {recommendedSplitter && (
                  <Alert
                    icon={<IconInfoCircle size={16} />}
                    color="green"
                    variant="light"
                    title="Recommended Splitter"
                  >
                    <Text size="sm">
                      <strong>Configuration-based Recommendation:</strong><br />
                      {recommendedSplitter.reason}
                    </Text>
                    <Button
                      size="xs"
                      variant="light"
                      mt="sm"
                      onClick={() => {
                        form.setFieldValue('splitter_type', recommendedSplitter.type);
                        notifications.show({
                          title: 'Splitter Applied',
                          message: `Applied recommended ${recommendedSplitter.type}-based splitting strategy`,
                          color: 'green',
                          autoClose: 3000,
                        });
                      }}
                    >
                      Apply Recommendation
                    </Button>
                  </Alert>
                )}

                <Box>
                  <Text fw={500} size="sm" mb="sm">Splitting Strategy</Text>
                  <Radio.Group
                    value={form.values.splitter_type}
                    onChange={(value) => {
                      form.setFieldValue('splitter_type', value);

                      // Set default values based on splitter type
                      if (value === 'html') {
                        form.setFieldValue('sections_to_split_on', [
                          ['h1', 'Header 1'],
                          ['h2', 'Header 2'],
                          ['h3', 'Header 3'],
                          ['h4', 'Header 4']
                        ]);
                      } else if (value === 'document') {
                        form.setFieldValue('headers_to_split_on', [
                          ['#', 'Header 1'],
                          ['##', 'Header 2'],
                          ['###', 'Header 3'],
                          ['####', 'Header 4']
                        ]);
                      }
                    }}
                  >
                    <Stack gap="sm">
                      <Radio
                        value="text"
                        label={
                          <Group gap="xs">
                            <Text>Text-based splitting (Token-based chunking)</Text>
                            {recommendedSplitter?.type === 'text' && (
                              <Text size="xs" c="green" fw={500}>✓ Recommended</Text>
                            )}
                          </Group>
                        }
                      />
                      <Radio
                        value="document"
                        label={
                          <Group gap="xs">
                            <Text>Document-structured splitting (Markdown headers)</Text>
                            {recommendedSplitter?.type === 'document' && (
                              <Text size="xs" c="green" fw={500}>✓ Recommended</Text>
                            )}
                          </Group>
                        }
                      />
                      <Radio
                        value="html"
                        label={
                          <Group gap="xs">
                            <Text>HTML-structured splitting (HTML headers)</Text>
                            {recommendedSplitter?.type === 'html' && (
                              <Text size="xs" c="green" fw={500}>✓ Recommended</Text>
                            )}
                          </Group>
                        }
                      />
                    </Stack>
                  </Radio.Group>
                </Box>

                {form.values.splitter_type === 'text' && (
                  <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                    <NumberInput
                      label="Chunk Size (Tokens)"
                      placeholder="256"
                      required
                      description="Size of text chunks in tokens. Recommended: 256-512 tokens for balanced context and precision"
                      min={64}
                      max={4096}
                      {...form.getInputProps('chunk_size')}
                      onChange={(value) => {
                        const numValue = typeof value === 'number' ? value : parseInt(value) || 0;
                        form.setFieldValue('chunk_size', numValue);
                        // Auto-calculate overlap as 12.5% of chunk size, but cap at 50%
                        const calculatedOverlap = Math.min(Math.round(numValue * 0.125), Math.floor(numValue / 2));
                        form.setFieldValue('chunk_overlap', calculatedOverlap);

                        // Notify user about auto-calculation
                        notifications.show({
                          title: 'Overlap Auto-Calculated',
                          message: `Chunk overlap automatically set to ${calculatedOverlap} tokens (${((calculatedOverlap / numValue) * 100).toFixed(1)}% of chunk size)`,
                          color: 'blue',
                          autoClose: 3000,
                        });
                      }}
                    />

                    <NumberInput
                      label="Chunk Overlap (Tokens)"
                      placeholder="32"
                      required
                      description="Overlap between consecutive chunks in tokens. Auto-calculated as 12.5% of chunk size, but can be manually adjusted"
                      min={0}
                      max={Math.floor(form.values.chunk_size / 2)}
                      {...form.getInputProps('chunk_overlap')}
                      onChange={(value) => {
                        const numValue = typeof value === 'number' ? value : parseInt(value) || 0;
                        form.setFieldValue('chunk_overlap', numValue);

                        // Notify user about manual overlap change
                        const percentage = ((numValue / form.values.chunk_size) * 100).toFixed(1);
                        notifications.show({
                          title: 'Overlap Updated',
                          message: `Chunk overlap set to ${numValue} tokens (${percentage}% of chunk size)`,
                          color: 'green',
                          autoClose: 2000,
                        });
                      }}
                    />
                  </SimpleGrid>
                )}

                {form.values.splitter_type === 'document' && (
                  <Stack gap="md">
                    <Alert color="blue" title="Chunk Size Configuration" icon={<IconInfoCircle />}>
                      When using document structure splitting, each header section is split into chunks.
                      The chunk size and overlap are automatically calculated to use 95% of your embedding model's capacity (leaving 5% safety buffer).
                      {embeddingMaxTokens && (
                        <>
                          <br /><br />
                          <strong>Embedding Model Max Tokens: {embeddingMaxTokens.toLocaleString()}</strong><br />
                          <strong>Maximum Allowed Total: {recommendedChunkConfig.maxAllowed.toLocaleString()} tokens</strong> (95% of max, 5% safety buffer)<br />
                          <strong>Recommended Chunk Size: {recommendedChunkConfig.chunkSize.toLocaleString()} tokens</strong> (82.5% of max)<br />
                          <strong>Recommended Overlap: {recommendedChunkConfig.chunkOverlap.toLocaleString()} tokens</strong> (12.5% of max)<br />
                          <strong>Total: {(recommendedChunkConfig.chunkSize + recommendedChunkConfig.chunkOverlap).toLocaleString()} tokens</strong> ≤ {recommendedChunkConfig.maxAllowed.toLocaleString()} tokens ✓
                        </>
                      )}
                      {!embeddingMaxTokens && (
                        <>
                          <br /><br />
                          <Text size="sm" c="orange">
                            ⚠️ No embedding model selected yet. Please go back to the Embedding Model step to select a provider first.
                            Using default values (256 chunk size, 32 overlap).
                          </Text>
                        </>
                      )}
                    </Alert>

                    {embeddingMaxTokens && (
                      <Button
                        size="sm"
                        variant="light"
                        onClick={() => {
                          form.setFieldValue('chunk_size', recommendedChunkConfig.chunkSize);
                          form.setFieldValue('chunk_overlap', recommendedChunkConfig.chunkOverlap);
                          notifications.show({
                            title: 'Recommended Values Applied',
                            message: `Chunk size set to ${recommendedChunkConfig.chunkSize} tokens, overlap set to ${recommendedChunkConfig.chunkOverlap} tokens (based on embedding model's ${embeddingMaxTokens} max tokens)`,
                            color: 'green',
                            autoClose: 4000,
                          });
                        }}
                      >
                        Apply Recommended Values
                      </Button>
                    )}

                    <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                      <NumberInput
                        label="Chunk Size (Tokens)"
                        placeholder={recommendedChunkConfig.chunkSize.toString()}
                        required
                        description={embeddingMaxTokens
                          ? `Recommended: ${recommendedChunkConfig.chunkSize} tokens (based on ${embeddingMaxTokens} max tokens)`
                          : "Maximum size of chunks within each section. Prevents exceeding embedding token limits."
                        }
                        min={64}
                        max={embeddingMaxTokens ? embeddingMaxTokens : 4096}
                        {...form.getInputProps('chunk_size')}
                        onChange={(value) => {
                          const numValue = typeof value === 'number' ? value : parseInt(value) || 0;
                          form.setFieldValue('chunk_size', numValue);
                          // Auto-calculate overlap as 12.5% of chunk size, but cap at 50%
                          const calculatedOverlap = Math.min(Math.round(numValue * 0.125), Math.floor(numValue / 2));
                          form.setFieldValue('chunk_overlap', calculatedOverlap);

                          // Notify user about auto-calculation
                          notifications.show({
                            title: 'Overlap Auto-Calculated',
                            message: `Chunk overlap automatically set to ${calculatedOverlap} tokens (${((calculatedOverlap / numValue) * 100).toFixed(1)}% of chunk size)`,
                            color: 'blue',
                            autoClose: 3000,
                          });
                        }}
                      />

                      <NumberInput
                        label="Chunk Overlap (Tokens)"
                        placeholder={recommendedChunkConfig.chunkOverlap.toString()}
                        required
                        description={`Recommended: ${recommendedChunkConfig.chunkOverlap} tokens (12.5% of chunk size)`}
                        min={0}
                        max={Math.floor(form.values.chunk_size / 2)}
                        {...form.getInputProps('chunk_overlap')}
                        onChange={(value) => {
                          const numValue = typeof value === 'number' ? value : parseInt(value) || 0;
                          form.setFieldValue('chunk_overlap', numValue);

                          // Notify user about manual overlap change
                          const percentage = ((numValue / form.values.chunk_size) * 100).toFixed(1);
                          notifications.show({
                            title: 'Overlap Updated',
                            message: `Chunk overlap set to ${numValue} tokens (${percentage}% of chunk size)`,
                            color: 'green',
                            autoClose: 2000,
                          });
                        }}
                      />
                    </SimpleGrid>

                    {/* Show warning if chunk size + overlap exceeds 95% of max tokens */}
                    {embeddingMaxTokens && (form.values.chunk_size + form.values.chunk_overlap) > recommendedChunkConfig.maxAllowed && (
                      <Alert color="red" icon={<IconAlertTriangle />}>
                        <Text size="sm">
                          <strong>Warning: Total tokens exceed recommended limit!</strong><br />
                          Chunk size ({form.values.chunk_size.toLocaleString()}) + overlap ({form.values.chunk_overlap.toLocaleString()}) = {(form.values.chunk_size + form.values.chunk_overlap).toLocaleString()} tokens<br />
                          This exceeds the recommended maximum of {recommendedChunkConfig.maxAllowed.toLocaleString()} tokens (95% of {embeddingMaxTokens.toLocaleString()}, leaving 5% safety buffer).<br />
                          Please reduce chunk size or overlap to avoid potential embedding failures.
                        </Text>
                      </Alert>
                    )}
                  </Stack>
                )}

                {(form.values.splitter_type === 'document' || form.values.splitter_type === 'html') && (
                  <Stack gap="md">
                    <Group gap="xs" align="center">
                      <Text fw={500} size="sm">
                        {form.values.splitter_type === 'html' ? 'Sections to Split On' : 'Headers to Split On'}
                      </Text>
                      <Tooltip
                        label={
                          form.values.splitter_type === 'html'
                            ? 'Documents will be split based on HTML sections. Configure which HTML elements to use for splitting below.'
                            : 'Documents will be split based on markdown headers. Configure which header levels to use for splitting below.'
                        }
                        multiline
                        w={300}
                      >
                        <ActionIcon size="xs" variant="transparent" color="blue">
                          <IconInfoCircle size={14} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>

                    <Box>
                      <Text size="xs" c="dimmed" mb="sm">
                        {form.values.splitter_type === 'html'
                          ? 'Define which HTML section patterns should trigger document splitting. Each section creates a new chunk.'
                          : 'Define which markdown header patterns should trigger document splitting. Each header creates a new chunk.'
                        }
                      </Text>

                      <Stack gap="xs">
                        {(form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on).map((header, index) => (
                          <Group key={index} gap="xs">
                            <TextInput
                              placeholder={form.values.splitter_type === 'html' ? 'Element (e.g., h1, p, div)' : 'Pattern (e.g., #)'}
                              value={header[0]}
                              onChange={(e) => {
                                const fieldName = form.values.splitter_type === 'html' ? 'sections_to_split_on' : 'headers_to_split_on';
                                const currentValues = form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on;
                                const newValues = [...currentValues];
                                newValues[index] = [e.target.value, header[1]];
                                form.setFieldValue(fieldName, newValues);
                              }}
                              style={{ flex: '0 0 100px' }}
                            />
                            <TextInput
                              placeholder="Label (e.g., Header 1)"
                              value={header[1]}
                              onChange={(e) => {
                                const fieldName = form.values.splitter_type === 'html' ? 'sections_to_split_on' : 'headers_to_split_on';
                                const currentValues = form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on;
                                const newValues = [...currentValues];
                                newValues[index] = [header[0], e.target.value];
                                form.setFieldValue(fieldName, newValues);
                              }}
                              style={{ flex: 1 }}
                            />
                            <Button
                              size="xs"
                              variant="subtle"
                              color="red"
                              onClick={() => {
                                const fieldName = form.values.splitter_type === 'html' ? 'sections_to_split_on' : 'headers_to_split_on';
                                const currentValues = form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on;
                                const newValues = currentValues.filter((_, i) => i !== index);
                                form.setFieldValue(fieldName, newValues);
                              }}
                              disabled={(form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on).length <= 1}
                            >
                              Remove
                            </Button>
                          </Group>
                        ))}

                        <Button
                          size="xs"
                          variant="light"
                          onClick={() => {
                            const fieldName = form.values.splitter_type === 'html' ? 'sections_to_split_on' : 'headers_to_split_on';
                            const currentValues = form.values.splitter_type === 'html' ? form.values.sections_to_split_on : form.values.headers_to_split_on;
                            const currentCount = currentValues.length;
                            const nextLevel = currentCount + 1;

                            let pattern, label;
                            if (form.values.splitter_type === 'html') {
                              // HTML elements: h1, h2, h3, h4, p, div, section, article
                              const htmlElements = ['h1', 'h2', 'h3', 'h4', 'p', 'div', 'section', 'article'];
                              if (nextLevel <= htmlElements.length) {
                                pattern = htmlElements[nextLevel - 1];
                                label = nextLevel <= 4 ? `Header ${nextLevel}` :
                                  pattern === 'p' ? 'Paragraph' :
                                    pattern === 'div' ? 'Division' :
                                      pattern === 'section' ? 'Section' : 'Article';
                              } else {
                                pattern = `h${nextLevel}`;
                                label = `Header ${nextLevel}`;
                              }
                            } else { // document (markdown)
                              pattern = '#'.repeat(nextLevel);
                              label = `Header ${nextLevel}`;
                            }

                            const newValues = [...currentValues, [pattern, label]];
                            form.setFieldValue(fieldName, newValues);
                          }}
                        >
                          {form.values.splitter_type === 'html' ? 'Add Section Level' : 'Add Header Level'}
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                )}

                {/* Show warning if user selects non-recommended splitter */}
                {recommendedSplitter && form.values.splitter_type !== recommendedSplitter.type && (
                  <Alert icon={<IconAlertTriangle size={16} />} color="orange" variant="light">
                    <Text size="sm">
                      <strong>Non-Recommended Splitter Selected</strong><br />
                      Your source configuration outputs {selectedConfig?.output_format} format, but you've selected {form.values.splitter_type}-based splitting.
                      {recommendedSplitter.type === 'document'
                        ? ' Consider using document-structured splitting to better preserve content hierarchy from markdown formatting.'
                        : ' Consider using text-based splitting for more consistent chunking of HTML content.'
                      }
                    </Text>
                  </Alert>
                )}

              </Stack>
            )}

            {activeStep === 4 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  <Text size="sm">
                    <strong>Step 5: Job Processing Configuration</strong><br />
                    Configure how the job will process documents, including batch size and output file settings.
                  </Text>
                </Alert>

                <NumberInput
                  label="Batch Size"
                  placeholder="100"
                  min={1}
                  max={1000}
                  required
                  description="Number of documents to process in each batch. Be careful not to increase this too much as it could exceed the maximum token limit when generating embeddings."
                  {...form.getInputProps('batch_size')}
                />

                <Divider my="md" />

                <Switch
                  label="Save extracted content to files"
                  description="Save the extracted and processed content to files for backup or review purposes"
                  {...form.getInputProps('save_to_file', { type: 'checkbox' })}
                />

                <Switch
                  label="Write consolidated file (memory intensive)"
                  description="Write all content to a single consolidated file. Uses more memory but creates one complete file."
                  disabled={!form.values.save_to_file}
                  {...form.getInputProps('write_consolidated_file', { type: 'checkbox' })}
                />

                <Divider my="md" />

                <Switch
                  label="Clear collection data before starting"
                  description="Clear all existing data from the collection before starting the job. This will remove all previously processed documents from the collection."
                  {...form.getInputProps('clear_collection_before_start', { type: 'checkbox' })}
                />

                <Switch
                  label="Check duplicates before insert"
                  description="Check for duplicate URLs before inserting new records. Skips URLs that already exist in the collection."
                  {...form.getInputProps('check_duplicates_before_insert', { type: 'checkbox' })}
                />
              </Stack>
            )}

            {activeStep === 5 && (
              <Stack gap="md">
                <Alert icon={<IconInfoCircle size={16} />} color="green" variant="light">
                  <Text size="sm">
                    <strong>{isEditMode ? 'Review & Update Job' : 'Review & Create Job'}</strong><br />
                    {isEditMode
                      ? 'Review your job configuration before updating. Verify all settings are correct, including the knowledge source, vector database collection, embedding model, and chunking parameters. Changes will be applied to the job settings.'
                      : 'Review your job configuration before creating. Verify all settings are correct, including the knowledge source, vector database collection, embedding model, and chunking parameters. You can always edit these settings later after the job is created.'
                    }
                  </Text>
                </Alert>

                {/* Job Overview */}
                <Stack gap="md">
                  <Text size="lg" fw={500}>Job Overview</Text>
                  <SimpleGrid cols={2}>
                    <Box>
                      <Text size="sm" fw={500} mb="xs">Configuration</Text>
                      <Text size="sm" c="dimmed">{getConfigName(form.values.config_id)}</Text>
                    </Box>

                    <Box>
                      <Text size="sm" fw={500} mb="xs">Job Name</Text>
                      <Text size="sm" c="dimmed">{form.values.name}</Text>
                    </Box>
                  </SimpleGrid>
                </Stack>

                {/* Vector DB Collection Configuration */}
                <Stack gap="md">
                  <Text size="lg" fw={500}>Vector DB Collection</Text>
                  <SimpleGrid cols={2}>
                    <Box>
                      <Text size="sm" fw={500} mb="xs">Collection Type</Text>
                      <Text size="sm" c="dimmed">{form.values.use_existing_collection ? 'Existing Collection' : 'New Collection'}</Text>
                    </Box>

                    {form.values.use_existing_collection ? (
                      <Box>
                        <Text size="sm" fw={500} mb="xs">Selected Collection</Text>
                        <Text size="sm" c="dimmed">{form.values.existing_collection_id}</Text>
                      </Box>
                    ) : (
                      <Box>
                        <Text size="sm" fw={500} mb="xs">Collection Name</Text>
                        <Text size="sm" c="dimmed">{form.values.collection_name}</Text>
                      </Box>
                    )}

                    {!form.values.use_existing_collection && (
                      <>
                        <Box>
                          <Text size="sm" fw={500} mb="xs">Provider</Text>
                          <Text size="sm" c="dimmed">{getProviderName(form.values.embedding_model_provider_id)}</Text>
                        </Box>

                        <Box>
                          <Text size="sm" fw={500} mb="xs">Model</Text>
                          <Text size="sm" c="dimmed">{form.values.embedding_model_name}</Text>
                        </Box>

                        <Box>
                          <Text size="sm" fw={500} mb="xs">Vector Dimension</Text>
                          <Text size="sm" c="dimmed">{form.values.vector_dimension}</Text>
                        </Box>
                      </>
                    )}
                  </SimpleGrid>
                </Stack>

                {/* Document Splitting Configuration */}
                <Stack gap="md">
                  <Text size="lg" fw={500}>Document Splitting</Text>

                  {/* Show configuration alignment */}
                  {selectedConfig && (
                    <Alert
                      icon={<IconInfoCircle size={16} />}
                      color={recommendedSplitter && form.values.splitter_type === recommendedSplitter.type ? "green" : "orange"}
                      variant="light"
                    >
                      <Text size="sm">
                        <strong>Configuration Alignment:</strong><br />
                        Source outputs <strong>{selectedConfig.output_format}</strong> format →
                        {recommendedSplitter && form.values.splitter_type === recommendedSplitter.type
                          ? ` ✓ Using recommended ${recommendedSplitter.type}-based splitting`
                          : ` ⚠ Using ${form.values.splitter_type}-based splitting (${recommendedSplitter ? 'not recommended' : 'no recommendation available'})`
                        }
                      </Text>
                    </Alert>
                  )}

                  <SimpleGrid cols={2}>
                    <Box>
                      <Text size="sm" fw={500} mb="xs">Splitter Type</Text>
                      <Text size="sm" c="dimmed">
                        {form.values.splitter_type === 'text'
                          ? 'Text-based splitting'
                          : form.values.splitter_type === 'document'
                            ? 'Markdown-structured splitting'
                            : 'HTML-structured splitting'
                        }
                      </Text>
                    </Box>

                    {form.values.splitter_type === 'text' && (
                      <>
                        <Box>
                          <Text size="sm" fw={500} mb="xs">Chunk Size</Text>
                          <Text size="sm" c="dimmed">{form.values.chunk_size} tokens</Text>
                        </Box>

                        <Box>
                          <Text size="sm" fw={500} mb="xs">Chunk Overlap</Text>
                          <Text size="sm" c="dimmed">{form.values.chunk_overlap} tokens ({(form.values.chunk_overlap / form.values.chunk_size * 100).toFixed(1)}%)</Text>
                        </Box>
                      </>
                    )}

                    {(form.values.splitter_type === 'document' || form.values.splitter_type === 'html') && (
                      <Box>
                        <Text size="sm" fw={500} mb="xs">Splitting Strategy</Text>
                        <Text size="sm" c="dimmed">
                          {form.values.splitter_type === 'html'
                            ? 'HTML section-based splitting'
                            : 'Markdown header-based splitting'
                          }
                        </Text>
                      </Box>
                    )}
                  </SimpleGrid>
                </Stack>

                {/* Processing Configuration */}
                <Stack gap="md">
                  <Text size="lg" fw={500}>Processing Settings</Text>
                  <SimpleGrid cols={2}>
                    <Box>
                      <Text size="sm" fw={500} mb="xs">Batch Size</Text>
                      <Text size="sm" c="dimmed">{form.values.batch_size} documents</Text>
                    </Box>

                    <Box>
                      <Text size="sm" fw={500} mb="xs">Save to File</Text>
                      <Text size="sm" c="dimmed">{form.values.save_to_file ? 'Yes' : 'No'}</Text>
                    </Box>

                    <Box>
                      <Text size="sm" fw={500} mb="xs">Consolidated File</Text>
                      <Text size="sm" c="dimmed">{form.values.write_consolidated_file ? 'Yes' : 'No'}</Text>
                    </Box>

                    <Box>
                      <Text size="sm" fw={500} mb="xs">Clear Collection Before Start</Text>
                      <Text size="sm" c="dimmed">{form.values.clear_collection_before_start ? 'Yes' : 'No'}</Text>
                    </Box>

                    <Box>
                      <Text size="sm" fw={500} mb="xs">Check Duplicates Before Insert</Text>
                      <Text size="sm" c="dimmed">{form.values.check_duplicates_before_insert ? 'Yes' : 'No'}</Text>
                    </Box>
                  </SimpleGrid>
                </Stack>

                {form.values.description && (
                  <Box>
                    <Text size="sm" fw={500} mb="xs">Description</Text>
                    <Text size="sm" c="dimmed">{form.values.description}</Text>
                  </Box>
                )}
              </Stack>
            )}
          </ColorfulVerticalStepper>

          <Group justify="space-between" mt="xl">
            <Button type="button" variant="subtle" onClick={handleCancel}>
              Cancel
            </Button>

            <Group>
              <Button
                type="button"
                variant="default"
                onClick={prevStep}
                disabled={activeStep === 0}
              >
                Previous
              </Button>

              {activeStep < 5 ? (
                <Button
                  type="button"
                  onClick={() => {
                    console.log('Next button clicked, current activeStep:', activeStep);
                    nextStep();
                  }}
                >
                  Next
                </Button>
              ) : (
                <Button
                  type="submit"
                  loading={isCreatingSplitter || (isEditMode ? updateJobMutation.isPending : createJobMutation.isPending)}
                  leftSection={<IconWand size={16} />}
                  onClick={() => {
                    console.log('Create Job button clicked, current activeStep:', activeStep);
                    setIsExplicitSubmit(true);
                  }}
                >
                  {isCreatingSplitter
                    ? 'Configuring Splitter...'
                    : (isEditMode ? 'Update Job' : 'Create Job')
                  }
                </Button>
              )}
            </Group>
          </Group>
        </form>
      </Paper>
    </Page>
  );
}
