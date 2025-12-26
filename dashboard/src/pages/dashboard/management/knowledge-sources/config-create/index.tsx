import { useCreateContentFilter, useGetEnabledContentFilters } from '@/api/resources/content-filters';
import { useCreateKnowledgeSourceConfig } from '@/api/resources/knowledge-sources';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useListConfluenceCredentials } from '@/api/resources/confluence-credentials';
import { ColorfulVerticalStepper, StepConfig } from '@/components/colorful-vertical-stepper';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { useTestCssSelectors } from '@/hooks/use-knowledge-source-test';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Divider,
  FileInput,
  Group,
  Loader,
  Modal,
  NumberInput,
  Radio,
  ScrollArea,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
  IconChevronRight,
  IconClipboardCheck,
  IconCode,
  IconCopy,
  IconFileText,
  IconFilter,
  IconInfoCircle,
  IconPlus,
  IconSettings,
  IconWand,
  IconWorld,
  IconX,
  IconBook
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Create Configuration' },
];

const contentSourceTypes = [
  { value: 'web_scraping', label: 'Web Scraping', description: 'Crawl websites and web pages' },
  { value: 'local_files', label: 'Local Files', description: 'Upload HTML and Markdown files' },
  { value: 'confluence', label: 'Confluence', description: 'Extract from Confluence Cloud API' },
];

const webScrapingModes = [
  { value: 'single_page', label: 'Single Page' },
  { value: 'multiple_pages', label: 'Multiple Pages (Upload URLs)' },
  { value: 'website', label: 'Website Crawler' },
];

const localFileModes = [
  { value: 'html_files', label: 'HTML Files' },
  { value: 'markdown_files', label: 'Markdown Files' },
  { value: 'pdf_files', label: 'PDF Files' },
  { value: 'docx_files', label: 'DOCX Files' },
  { value: 'txt_files', label: 'TXT Files' },
];

const confluenceModes = [
  { value: 'space_pages', label: 'Space Pages', description: 'Extract all pages from specific spaces' },
  { value: 'specific_pages', label: 'Specific Pages', description: 'Extract individual pages by ID' },
  { value: 'pages_with_label', label: 'Pages with Labels', description: 'Extract pages matching labels' },
  { value: 'recently_modified', label: 'Recently Modified', description: 'Extract recently changed pages' },
];

export default function CreateKnowledgeSourceConfig() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [hasReachedFinalStep, setHasReachedFinalStep] = useState(false);
  const [createFilterModalOpened, setCreateFilterModalOpened] = useState(false);
  const [isCreatingFilter, setIsCreatingFilter] = useState(false);
  const [newSelector, setNewSelector] = useState('');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isTestSectionVisible, setIsTestSectionVisible] = useState(false);
  const [isContentFilterTestVisible, setIsContentFilterTestVisible] = useState(false);
  const [testOutputFormat, setTestOutputFormat] = useState<'html' | 'markdown'>('html');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Copy function for test results
  const handleCopyResult = async () => {
    if (testResult) {
      try {
        await navigator.clipboard.writeText(testResult);
        notifications.show({
          title: 'Copied!',
          message: 'Test result copied to clipboard',
          color: 'green',
        });
      } catch (err) {
        notifications.show({
          title: 'Copy failed',
          message: 'Failed to copy to clipboard',
          color: 'red',
        });
      }
    }
  };

  // HTML Analyzer hook with modal

  const createConfigMutation = useCreateKnowledgeSourceConfig();
  const { data: contentFilters, isLoading: filtersLoading, refetch: refetchFilters } = useGetEnabledContentFilters();
  const testSelectorsMutation = useTestCssSelectors();
  const { data: allProviders, isLoading: providersLoading } = useGetActiveModelProviders();
  const createFilterMutation = useCreateContentFilter();
  const { data: confluenceCredentials, isLoading: confluenceCredentialsLoading } = useListConfluenceCredentials();

  // Filter for generative providers
  const generativeProviders = allProviders?.filter((provider: any) =>
    provider.generative !== null && provider.generative !== undefined
  ) || [];

  const form = useForm({
    initialValues: {
      name: '',
      description: '',
      content_source_type: 'web_scraping' as 'web_scraping' | 'local_files' | 'confluence',
      url: '',
      scraping_mode: 'website' as 'single_page' | 'multiple_pages' | 'website' | 'html_files' | 'markdown_files' | 'pdf_files' | 'docx_files' | 'txt_files' | 'space_pages' | 'specific_pages' | 'pages_with_label' | 'recently_modified',
      url_source: {
        file_name: undefined as string | undefined,
        urls: [] as string[],
      },
      allowed_subdomains: [] as string[],
      blocked_subdomains: [] as string[],
      url_patterns: [] as any[],
      crawl_depth: 4,
      target_elements: [] as string[],
      content_filter_threshold: 0.6,
      llm_content_filter_id: null as string | null,
      output_format: 'html' as 'html' | 'markdown',
      markdown_generation: 'standard' as 'standard' | 'llm',
      local_files: [] as any[],
      file_types: [] as string[],
      confluence_credential_id: null as string | null,
      confluence_mode: 'space_pages' as 'space_pages' | 'specific_pages' | 'pages_with_label' | 'recently_modified',
      confluence_config: {
        cloud_url: '',
        username_or_email: '',
        api_token: '',
        space_keys: [] as string[],
        page_ids: [] as string[],
        labels: [] as string[],
        include_attachments: false,
        include_comments: false,
        expand_child_pages: true,
      }
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      url: (value, values) => {
        // URL not required for local files or multiple_pages mode
        if (values.content_source_type === 'local_files' || values.scraping_mode === 'multiple_pages') {
          return null;
        }

        // For web scraping modes that need URLs
        if (!value) {
          return 'URL is required';
        }

        // Validate URL format
        try {
          const url = new URL(value);
          if (!url.protocol.startsWith('http')) {
            return 'URL must start with http:// or https://';
          }
          return null;
        } catch (e) {
          return 'Please enter a valid URL (e.g., https://example.com)';
        }
      },
    },
  });

  const updateCssSelector = (parts: Array<{ type: string; selector: string }>) => {
    const selector = parts
      .filter(part => part.type) // Only include parts with a type
      .map(part => {
        let selector = part.type;
        if (part.selector) {
          // Add class or id selector
          if (part.selector.startsWith('.')) {
            selector += part.selector;
          } else if (part.selector.startsWith('#')) {
            selector += part.selector;
          } else {
            // Assume it's a class if no prefix
            selector += '.' + part.selector;
          }
        }
        return selector;
      })
      .join(' > ');

    // CSS selector is no longer used - using target_elements instead
  };

  const isFormValid = (): boolean => {
    console.log('🔍 Checking form validity:', {
      name: form.values.name,
      content_source_type: form.values.content_source_type,
      scraping_mode: form.values.scraping_mode,
      has_files: form.values.local_files?.length,
      has_url: form.values.url
    });

    // Check basic required fields
    if (!form.values.name) {
      console.log('❌ Form invalid: No name');
      return false;
    }

    // For web scraping, check scraping mode and URL requirements
    if (form.values.content_source_type === 'web_scraping') {
      if (!form.values.scraping_mode) {
        console.log('❌ Form invalid: No scraping mode for web scraping');
        return false;
      }

      if (form.values.scraping_mode === 'single_page' && !form.values.url) {
        console.log('❌ Form invalid: No URL for single page');
        return false;
      }
      if (form.values.scraping_mode === 'website' && !form.values.url) {
        console.log('❌ Form invalid: No URL for website');
        return false;
      }
      if (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length === 0) {
        console.log('❌ Form invalid: No URLs for multiple pages');
        return false;
      }
    }

    // For local files, check that files are uploaded
    if (form.values.content_source_type === 'local_files') {
      if (!form.values.local_files || form.values.local_files.length === 0) {
        console.log('❌ Form invalid: No files uploaded for local files');
        return false;
      }
      if (!form.values.scraping_mode) {
        console.log('❌ Form invalid: No scraping mode (file type) selected');
        return false;
      }
    }

    // For Confluence, check that credential is selected
    if (form.values.content_source_type === 'confluence') {
      if (!form.values.confluence_credential_id) {
        console.log('❌ Form invalid: No Confluence credential selected');
        return false;
      }
      if (!form.values.confluence_mode) {
        console.log('❌ Form invalid: No Confluence mode selected');
        return false;
      }
    }

    console.log('✅ Form is valid');
    return true;
  };

  const validateStep = (step: number): boolean => {
    // Get the current step configuration to validate based on label
    const currentStepLabel = stepConfigs[step]?.label;

    if (!currentStepLabel) {
      console.warn('⚠️ No step config found for step', step);
      return false;
    }

    console.log('🔍 Validating step:', { step, label: currentStepLabel });

    // Validate based on step label (not hardcoded index!)
    if (currentStepLabel?.includes('Basic Info')) {
      // Validate basic info
      if (!form.values.name) {
        console.log('❌ Validation failed: No name');
        return false;
      }

      if (form.values.content_source_type === 'web_scraping') {
        // Validate scraping config
        if (!form.values.scraping_mode) {
          console.log('❌ Validation failed: No scraping mode');
          return false;
        }

        // For single_page and website modes, validate URL
        if (form.values.scraping_mode === 'single_page' || form.values.scraping_mode === 'website') {
          if (!form.values.url) {
            console.log('❌ Validation failed: No URL');
            return false;
          }

          // Validate URL format
          try {
            const url = new URL(form.values.url);
            if (!url.protocol.startsWith('http')) {
              console.log('❌ Validation failed: Invalid URL protocol');
              return false;
            }
          } catch (e) {
            console.log('❌ Validation failed: Invalid URL format');
            return false; // Invalid URL format
          }
        }

        // For multiple_pages mode, check if URLs are uploaded
        if (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length === 0) {
          console.log('❌ Validation failed: No URLs uploaded');
          return false;
        }
      } else if (form.values.content_source_type === 'local_files') {
        // For local files, check if files are uploaded
        console.log('Local files validation:', {
          content_source_type: form.values.content_source_type,
          local_files: form.values.local_files,
          local_files_length: form.values.local_files?.length,
          scraping_mode: form.values.scraping_mode
        });
        if (!form.values.local_files || form.values.local_files.length === 0) {
          console.log('❌ Validation failed: No files uploaded');
          return false;
        }
      } else if (form.values.content_source_type === 'confluence') {
        // For Confluence, check if credential and mode are selected
        console.log('Confluence validation:', {
          content_source_type: form.values.content_source_type,
          confluence_credential_id: form.values.confluence_credential_id,
          confluence_mode: form.values.confluence_mode
        });
        if (!form.values.confluence_credential_id) {
          console.log('❌ Validation failed: No Confluence credential selected');
          return false;
        }
        if (!form.values.confluence_mode) {
          console.log('❌ Validation failed: No Confluence mode selected');
          return false;
        }
      }

      console.log('✅ Basic Info step valid');
      return true;
    }

    // Domain Filtering step (optional)
    if (currentStepLabel === 'Domain Filtering') {
      console.log('✅ Domain Filtering step valid (optional)');
      return true;
    }

    // Content Filter step (optional)
    if (currentStepLabel === 'Content Filter') {
      console.log('✅ Content Filter step valid (optional)');
      return true;
    }

    // Generation step (optional)
    if (currentStepLabel === 'Generation') {
      console.log('✅ Generation step valid (optional)');
      return true;
    }

    // Review step (always valid)
    if (currentStepLabel === 'Review') {
      console.log('✅ Review step valid');
      return true;
    }

    console.warn('⚠️ Unknown step label:', currentStepLabel);
    return false;
  };

  // Dynamic step configurations based on form state
  const getStepConfigs = (): StepConfig[] => {
    const isWebScraping = form.values.content_source_type === 'web_scraping';
    const isLocalFiles = form.values.content_source_type === 'local_files';
    const isConfluence = form.values.content_source_type === 'confluence';
    const scrapingMode = form.values.scraping_mode;

    // Step 1: Basic Info & Configuration (always first)
    const steps: StepConfig[] = [
      {
        label: isLocalFiles ? 'Basic Info & Upload' : isConfluence ? 'Basic Info & Confluence' : 'Basic Info & Scraping',
        description: isLocalFiles ? 'Name, description, files' : isConfluence ? 'Name, credential, mode' : 'Name, description, URL',
        icon: <IconSettings size={20} strokeWidth={2} />,
        color: '#45c9bb',
        gradientFrom: '#45c9bb',
        gradientTo: '#87cbbc'
      }
    ];

    // Step 2: Domain Filtering (only for web scraping)
    if (isWebScraping) {
      steps.push({
        label: 'Domain Filtering',
        description: 'Allowed/blocked domains',
        icon: <IconFilter size={20} strokeWidth={2} />,
        color: '#bbe773',
        gradientFrom: '#bbe773',
        gradientTo: '#9dd245'
      });
    }

    // Step 3: Content Filter (only for web scraping or HTML files)
    // HTML files need scraping/filtering, other file types don't
    const needsContentFilter = isWebScraping || scrapingMode === 'html_files';
    if (needsContentFilter) {
      steps.push({
        label: 'Content Filter',
        description: 'Target elements',
        icon: <IconCode size={20} strokeWidth={2} />,
        color: '#ddde65',
        gradientFrom: '#ddde65',
        gradientTo: '#bbe773'
      });
    }

    // Step 4: Generation (only for file types that need conversion)
    // Markdown files are already in final format, so they skip generation
    // HTML, PDF, DOCX, TXT need generation to decide output format
    // Confluence documents also need generation for format conversion
    const needsGeneration = isWebScraping ||
      isConfluence ||
      scrapingMode === 'html_files' ||
      scrapingMode === 'pdf_files' ||
      scrapingMode === 'docx_files' ||
      scrapingMode === 'txt_files';

    if (needsGeneration) {
      steps.push({
        label: 'Generation',
        description: 'Output format',
        icon: <IconWand size={20} strokeWidth={2} />,
        color: '#3bc57d',
        gradientFrom: '#3bc57d',
        gradientTo: '#45c9bb'
      });
    }

    // Step 5: Review (always last)
    steps.push({
      label: 'Review',
      description: 'Review and create',
      icon: <IconClipboardCheck size={20} strokeWidth={2} />,
      color: '#ae89ae',
      gradientFrom: '#ae89ae',
      gradientTo: '#87cbbc'
    });

    return steps;
  };

  // Make stepConfigs reactive to form changes
  const stepConfigs = useMemo(() => {
    const configs = getStepConfigs();
    console.log('🔄 Step configs updated:', {
      content_source_type: form.values.content_source_type,
      scraping_mode: form.values.scraping_mode,
      stepCount: configs.length,
      stepLabels: configs.map(s => s.label)
    });
    return configs;
  }, [form.values.content_source_type, form.values.scraping_mode]);

  const handleStepClick = (step: number) => {
    console.log('🔄 handleStepClick called', { currentStep: activeStep, targetStep: step });

    // Allow going back to previous steps
    if (step < activeStep) {
      console.log('🔄 Going back to step', step);
      setActiveStep(step);
      setHasReachedFinalStep(false); // Reset flag when going back
      return;
    }

    // Allow going to next step only if current step is completed
    if (step === activeStep + 1) {
      console.log('🔄 Trying to go to next step', { currentStep: activeStep, targetStep: step, isValid: validateStep(activeStep) });
      if (validateStep(activeStep)) {
        setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
        setActiveStep(step);
        console.log('🔄 Step changed via handleStepClick', { from: activeStep, to: step });
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

  const handleSubmit = async (values: typeof form.values) => {
    console.log('🚀 Submit started', {
      name: values.name,
      content_source_type: values.content_source_type,
      scraping_mode: values.scraping_mode,
      uploadedFilesCount: uploadedFiles.length
    });

    setIsSubmitting(true);
    try {
      // Build config data based on content source type
      // This is cleaner than deleting fields - we explicitly include what we need
      const isWebScraping = values.content_source_type === 'web_scraping';
      const isLocalFiles = values.content_source_type === 'local_files';

      // Base fields (always included)
      const configData: any = {
        name: values.name,
        description: values.description || undefined, // Send undefined (omitted) instead of empty string
        content_source_type: values.content_source_type,
        scraping_mode: values.scraping_mode,
        output_format: values.output_format,
      };

      // Add web scraping specific fields
      if (isWebScraping) {
        // URL (for single_page and website modes)
        if (values.scraping_mode === 'single_page' || values.scraping_mode === 'website') {
          configData.url = values.url;
        }

        // URL source (for multiple_pages mode)
        if (values.scraping_mode === 'multiple_pages' && values.url_source.urls.length > 0) {
          configData.url_source = {
            file_name: values.url_source.file_name || '',
            urls: values.url_source.urls
          };
        }

        // Crawl depth (for all web scraping modes)
        // single_page/multiple_pages typically use 0 (exact URLs only)
        // website mode uses higher values for recursive discovery
        configData.crawl_depth = values.crawl_depth;

        // Domain filtering
        if (values.allowed_subdomains && values.allowed_subdomains.length > 0) {
          configData.allowed_subdomains = values.allowed_subdomains;
        }
        if (values.blocked_subdomains && values.blocked_subdomains.length > 0) {
          configData.blocked_subdomains = values.blocked_subdomains;
        }

        // URL patterns
        if (values.url_patterns && values.url_patterns.length > 0) {
          configData.url_patterns = values.url_patterns;
        }

        // Target elements (CSS selectors)
        if (values.target_elements && values.target_elements.length > 0) {
          configData.target_elements = values.target_elements;
        }

        // Content filter
        if (values.llm_content_filter_id) {
          configData.llm_content_filter_id = values.llm_content_filter_id;
          configData.content_filter_threshold = values.content_filter_threshold;
        }
      }

      // Add local files specific fields (file_types will be set by backend based on uploaded files)
      if (isLocalFiles) {
        // file_types will be auto-detected by backend from uploaded files
        // No other fields needed for local files
      }

      // Add Confluence specific fields
      if (values.content_source_type === 'confluence') {
        configData.confluence_credential_id = values.confluence_credential_id;
        configData.confluence_config = {
          cloud_url: values.confluence_config.cloud_url,
          username_or_email: values.confluence_config.username_or_email,
          api_token: values.confluence_config.api_token,
          confluence_mode: values.confluence_mode,
          space_keys: values.confluence_config.space_keys.filter(k => k.trim()),
          page_ids: values.confluence_config.page_ids.filter(id => id.trim()),
          labels: values.confluence_config.labels.filter(l => l.trim()),
          include_attachments: values.confluence_config.include_attachments,
          include_comments: values.confluence_config.include_comments,
          expand_child_pages: values.confluence_config.expand_child_pages,
        };
      }

      console.log('📤 Prepared config data:', configData);
      console.log('✅ Has name?', 'name' in configData);
      console.log('✅ Name value:', configData.name);
      console.log('📁 Files count:', uploadedFiles.length);

      // Use unified mutation for both cases - it handles JSON and FormData automatically
      await createConfigMutation.mutateAsync({
        configData: configData,
        files: uploadedFiles.length > 0 ? uploadedFiles : undefined
      });

      notifications.show({
        title: 'Success',
        message: 'Knowledge source configuration created successfully',
        color: 'green',
      });
      navigate(paths.dashboard.management.knowledgeSources.configs);
    } catch (error: any) {
      console.log('🚨 Backend validation error:', error);
      console.log('🚨 Error details:', error.detail);

      let errorMessage = 'Failed to create configuration';
      if (error.detail && Array.isArray(error.detail)) {
        errorMessage = error.detail.map((err: any) => `${err.path?.join('.') || 'field'}: ${err.message}`).join(', ');
      } else if (error.message) {
        errorMessage = error.message;
      }

      notifications.show({
        title: 'Validation Error',
        message: errorMessage,
        color: 'red',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Content Filter Form
  const filterForm = useForm({
    initialValues: {
      name: '',
      description: '',
      enabled: true,
      llm_provider_id: '',
      llm_model_name: '',
      instruction: `Extract only the main technical documentation content.
Include:
- Key concepts and explanations
- Important code examples
- Essential technical details
- API references and guides

Exclude:
- Navigation elements
- Headers and footers
- Sidebars
- Advertisements
- Cookie notices
- Social media links

Format the output as clean markdown with proper code blocks and headers.`,
      chunk_token_threshold: 1000,
      temperature: 0.0,
      max_retries: 3,
      timeout_seconds: 30,
      verbose: false,
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      llm_provider_id: (value) => (!value ? 'Provider is required' : null),
      llm_model_name: (value) => (!value ? 'Model is required' : null),
      instruction: (value) => (!value ? 'Instruction is required' : null),
    },
  });

  const handleCreateFilter = async (values: typeof filterForm.values) => {
    setIsCreatingFilter(true);
    try {
      const result = await createFilterMutation.mutateAsync({ variables: values as any });
      notifications.show({
        title: 'Success',
        message: 'Content filter created successfully',
        color: 'green',
      });

      // Refetch filters and select the newly created one
      await refetchFilters();
      form.setFieldValue('llm_content_filter_id', result.id);

      // Close modal and reset form
      setCreateFilterModalOpened(false);
      filterForm.reset();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.message || 'Failed to create content filter',
        color: 'red',
      });
    } finally {
      setIsCreatingFilter(false);
    }
  };

  const handleTestSelectors = async () => {
    // Get test URL: use form URL or first URL from url_source for multiple_pages mode
    const testUrl = form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0 ? form.values.url_source.urls[0] : null);

    if (!testUrl || form.values.target_elements.length === 0) {
      return;
    }

    try {
      setIsTesting(true);
      setTestResult(null);

      const result = await testSelectorsMutation.mutateAsync({
        url: testUrl,
        target_elements: form.values.target_elements,
        scraping_mode: 'single_page',
        crawl_depth: 0,
        output_format: testOutputFormat,
      });

      if (result.success) {
        setTestResult(result.extracted_content);
      } else {
        setTestResult(`Error: ${result.error_message || 'Test failed'}`);
      }
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult(`Error: ${error instanceof Error ? error.message : 'Test failed'}`);
    } finally {
      setIsTesting(false);
    }
  };

  const handleTestGeneration = async () => {
    // Get test URL: use form URL or first URL from url_source for multiple_pages mode
    const testUrl = form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0 ? form.values.url_source.urls[0] : null);

    if (!testUrl || form.values.target_elements.length === 0) {
      return;
    }

    try {
      setIsTesting(true);
      setTestResult(null);

      // Auto-expand test section when testing
      setIsTestSectionVisible(true);

      // Determine output format based on configuration
      let outputFormat: 'html' | 'markdown' | 'llm_markdown' = 'html';
      let requestParams: any = {
        url: testUrl,
        target_elements: form.values.target_elements,
        scraping_mode: form.values.scraping_mode === 'multiple_pages' ? 'single_page' : form.values.scraping_mode,
        crawl_depth: form.values.scraping_mode === 'multiple_pages' ? 0 : form.values.crawl_depth,
      };

      if (form.values.output_format === 'html') {
        outputFormat = 'html';
      } else if (form.values.output_format === 'markdown') {
        if (form.values.markdown_generation === 'standard') {
          outputFormat = 'markdown';
          requestParams.content_filter_threshold = form.values.content_filter_threshold;
        } else if (form.values.markdown_generation === 'llm') {
          outputFormat = 'llm_markdown';
          // For LLM markdown, we need to get the filter instruction, provider, and model
          if (form.values.llm_content_filter_id && contentFilters) {
            const selectedFilter = contentFilters.find((f: any) => f.id === form.values.llm_content_filter_id);
            if (selectedFilter) {
              requestParams.llm_instructions = selectedFilter.instruction || 'Process the content';
              requestParams.llm_provider_id = selectedFilter.llm_provider_id;
              requestParams.llm_model_name = selectedFilter.llm_model_name;
            }
          }
        }
      }

      requestParams.output_format = outputFormat;

      console.log('Test request params:', requestParams);
      const result = await testSelectorsMutation.mutateAsync(requestParams);
      console.log('Test result:', result);

      if (result.success) {
        setTestResult(result.extracted_content);
        console.log('Test result set:', result.extracted_content);
      } else {
        setTestResult(`Error: ${result.error_message || 'Test failed'}`);
        console.log('Test error:', result.error_message);
      }
    } catch (error) {
      console.error('Generation test failed:', error);
      setTestResult(`Error: ${error instanceof Error ? error.message : 'Test failed'}`);
    } finally {
      setIsTesting(false);
    }
  };

  const nextStep = () => {
    const currentStepLabel = stepConfigs[activeStep]?.label;
    console.log('🔄 nextStep called', { activeStep, currentStepLabel, validateStep: validateStep(activeStep), totalSteps: stepConfigs.length });

    if (validateStep(activeStep)) {
      setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
      setActiveStep((current) => {
        const newStep = current < stepConfigs.length - 1 ? current + 1 : current;
        const newStepLabel = stepConfigs[newStep]?.label;
        console.log('🔄 Step changed', { from: current, to: newStep, fromLabel: currentStepLabel, toLabel: newStepLabel });

        // Reset flag when navigating to final step via Next button
        if (newStep === stepConfigs.length - 1) {
          setHasReachedFinalStep(false);
        }
        return newStep;
      });
    } else {
      // Show specific validation messages based on step label
      if (currentStepLabel?.includes('Basic Info')) {
        if (!form.values.name) {
          notifications.show({
            title: 'Validation Error',
            message: 'Please fill in the configuration name before proceeding.',
            color: 'red',
          });
        } else if (form.values.content_source_type === 'web_scraping') {
          if (!form.values.scraping_mode) {
            notifications.show({
              title: 'Validation Error',
              message: 'Please select a scraping mode before proceeding.',
              color: 'red',
            });
          } else if ((form.values.scraping_mode === 'single_page' || form.values.scraping_mode === 'website') && !form.values.url) {
            notifications.show({
              title: 'Validation Error',
              message: 'Please provide a URL before proceeding.',
              color: 'red',
            });
          } else if ((form.values.scraping_mode === 'single_page' || form.values.scraping_mode === 'website') && form.values.url) {
            // Check URL validity
            try {
              const url = new URL(form.values.url);
              if (!url.protocol.startsWith('http')) {
                notifications.show({
                  title: 'Invalid URL',
                  message: 'URL must start with http:// or https://',
                  color: 'red',
                });
              }
            } catch (e) {
              notifications.show({
                title: 'Invalid URL',
                message: 'Please enter a valid URL (e.g., https://example.com)',
                color: 'red',
              });
            }
          } else if (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length === 0) {
            notifications.show({
              title: 'Validation Error',
              message: 'Please upload a file with URLs before proceeding.',
              color: 'red',
            });
          }
        } else if (form.values.content_source_type === 'local_files') {
          if (!form.values.local_files || form.values.local_files.length === 0) {
            notifications.show({
              title: 'Validation Error',
              message: 'Please upload files before proceeding.',
              color: 'red',
            });
          }
        }
      }
    }
  };

  const prevStep = () => {
    setActiveStep((current) => (current > 0 ? current - 1 : current));
  };

  const handleFileUpload = (file: File | null) => {
    if (file) {
      processFile(file);
    } else {
      form.setFieldValue('url_source', { file_name: '', urls: [] });
    }
  };

  const isValidUrl = (string: string): boolean => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const processFile = (file: File) => {
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      notifications.show({
        title: 'File Too Large',
        message: `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds the 10MB limit`,
        color: 'red',
      });
      return;
    }

    // Check file extension
    if (!file.name.toLowerCase().endsWith('.txt')) {
      notifications.show({
        title: 'Invalid File Type',
        message: 'Please upload a .txt file only',
        color: 'red',
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const lines = content.split('\n');
      const urls = lines
        .map(line => line.trim())
        .filter(line => line && isValidUrl(line));

      // Check URL count (reasonable limit)
      if (urls.length > 50000) {
        notifications.show({
          title: 'Too Many URLs',
          message: `File contains ${urls.length} URLs. Please limit to 50,000 URLs or less`,
          color: 'red',
        });
        return;
      }

      form.setFieldValue('url_source', {
        file_name: file.name,
        urls: urls
      });

      notifications.show({
        title: 'File Uploaded Successfully',
        message: `Loaded ${urls.length} URLs from ${file.name} (${(file.size / 1024).toFixed(1)}KB)`,
        color: 'green',
      });
    };

    reader.onerror = () => {
      notifications.show({
        title: 'File Read Error',
        message: 'Failed to read the file. Please try again.',
        color: 'red',
      });
    };

    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      processFile(file);
    }
  };

  const handleLocalFilesDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    console.log('🚀 handleLocalFilesDrop called with files:', files);
    if (files.length > 0) {
      console.log('🚀 Processing dropped files:', files.map(f => ({ name: f.name, type: f.type, size: f.size })));

      // Store actual File objects for upload
      setUploadedFiles(files);

      // Create metadata for form display
      const localFiles = files.map((file, index) => ({
        file_id: `file_${Date.now()}_${index}`,
        original_filename: file.name,
        file_path: '', // Will be set after upload
        file_type: file.name.split('.').pop()?.toLowerCase() || 'html',
        file_size: file.size,
        upload_timestamp: new Date().toISOString(),
      }));
      console.log('🚀 Setting local_files via drag&drop to:', localFiles);
      console.log('🚀 Setting file_types via drag&drop to:', [...new Set(localFiles.map(f => f.file_type))]);
      form.setFieldValue('local_files', localFiles);
      form.setFieldValue('file_types', [...new Set(localFiles.map(f => f.file_type))]);

      // DON'T override scraping_mode - user already selected it via dropdown
      // The scraping_mode dropdown is already set to the file type

      // Set output format based on file types
      const fileTypes = [...new Set(localFiles.map(f => f.file_type))];
      if (fileTypes.includes('html') || fileTypes.includes('htm')) {
        // HTML files can have html, markdown, or llm_markdown output
        form.setFieldValue('output_format', 'html');
      } else {
        // All other file types (markdown, pdf, docx, txt) use markdown output
        form.setFieldValue('output_format', 'markdown');
      }
    } else {
      console.log('🚀 No files in drag&drop');
    }
  };

  const renderStepContent = () => {
    // Get current step configuration to determine what to render
    const currentStepLabel = stepConfigs[activeStep]?.label;

    // Render based on step label instead of hardcoded index
    // This ensures content matches the actual step shown, even when steps are skipped

    // Step 1: Basic Info (always first, but label changes based on content type)
    if (currentStepLabel?.includes('Basic Info')) {
      // This handles both "Basic Info & Scraping" and "Basic Info & Upload"
      return (
        <Stack id="step-0-basic-info" gap="md">
          <Title order={4}>Basic Information & Configuration</Title>
          <Text c="dimmed">
            {form.values.content_source_type === 'web_scraping'
              ? 'Configure your knowledge source and how to scrape content from the target website.'
              : form.values.content_source_type === 'local_files'
              ? 'Configure your knowledge source and upload local files.'
              : 'Configure your knowledge source and extract from Confluence API.'
            }
          </Text>

          {/* Content Source Type Selection */}
          <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconWorld size={18} color="var(--mantine-color-blue-6)" />
                <Text size="sm" fw={600} c="blue">Content Source Type</Text>
              </Group>

              <Radio.Group
                value={form.values.content_source_type}
                onChange={(value) => {
                  form.setFieldValue('content_source_type', value as 'web_scraping' | 'local_files' | 'confluence');
                  // Reset related fields when changing source type
                  if (value === 'local_files') {
                    form.setFieldValue('url', '');
                    form.setFieldValue('scraping_mode', 'html_files');
                    form.setFieldValue('output_format', 'markdown');
                  } else if (value === 'confluence') {
                    form.setFieldValue('url', '');
                    form.setFieldValue('local_files', []);
                    form.setFieldValue('file_types', []);
                    form.setFieldValue('scraping_mode', 'space_pages');
                    form.setFieldValue('confluence_mode', 'space_pages');
                  } else {
                    form.setFieldValue('local_files', []);
                    form.setFieldValue('file_types', []);
                    form.setFieldValue('scraping_mode', 'website');
                    form.setFieldValue('output_format', 'html');
                  }
                }}
              >
                <Group gap="xl">
                  {contentSourceTypes.map((type) => (
                    <Radio key={type.value} value={type.value} label={type.label} />
                  ))}
                </Group>
              </Radio.Group>
            </Stack>
          </Card>

          {/* Basic Information Section */}
          <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconSettings size={18} color="var(--mantine-color-blue-6)" />
                <Text size="sm" fw={600} c="blue">Basic Information</Text>
              </Group>

              <Group grow align="flex-start">
                <TextInput
                  label="Name"
                  placeholder="Enter a descriptive name"
                  required
                  {...form.getInputProps('name')}
                />

                <Textarea
                  label="Description"
                  placeholder="Describe what this configuration is for (optional)"
                  minRows={3}
                  {...form.getInputProps('description')}
                />
              </Group>
            </Stack>
          </Card>

          {/* Web Scraping Configuration Section */}
          {form.values.content_source_type === 'web_scraping' && (
            <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
              <Stack gap="md">
                <Group gap="xs" align="center">
                  <IconWorld size={18} color="var(--mantine-color-green-6)" />
                  <Text size="sm" fw={600} c="green">Web Scraping Configuration</Text>
                </Group>

                {/* Compact Row: Scraping Mode and URL */}
                <Group grow align="flex-start">
                  <Select
                    label="Scraping Mode"
                    placeholder="Select scraping mode"
                    required
                    data={webScrapingModes}
                    description={
                      form.values.scraping_mode === 'single_page'
                        ? 'Perfect for extracting content from a specific page or document (blog posts, documentation pages, product pages)'
                        : form.values.scraping_mode === 'multiple_pages'
                          ? 'Perfect for processing a predefined list of URLs from a file (batch processing, API documentation sets)'
                          : form.values.scraping_mode === 'website'
                            ? 'Perfect for crawling an entire website or domain automatically (documentation sites, blogs, e-commerce sites)'
                            : 'Select a scraping mode to see description'
                    }
                    {...form.getInputProps('scraping_mode')}
                  />

                  {form.values.scraping_mode === 'single_page' && (
                    <TextInput
                      label="Page URL"
                      placeholder="https://example.com/specific-page"
                      required
                      withAsterisk
                      {...form.getInputProps('url')}
                      description="Full public URL (e.g., https://docs.example.com/page). Private/auth pages may not work."
                    />
                  )}

                  {form.values.scraping_mode === 'website' && (
                    <TextInput
                      label="Website URL"
                      placeholder="https://example.com"
                      required
                      withAsterisk
                      {...form.getInputProps('url')}
                      description="Full public URL (e.g., https://example.com). Private/auth pages may not work."
                    />
                  )}
                </Group>

                {form.values.scraping_mode === 'multiple_pages' && (
                  <>
                    <div
                      onDragOver={handleDragOver}
                      onDragEnter={handleDragEnter}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      <FileInput
                        label="URL List File"
                        placeholder="Click to upload or drag and drop .txt file"
                        accept=".txt"
                        onChange={handleFileUpload}
                        description="Upload a text file with one URL per line (max 10MB, 50,000 URLs)"
                        leftSection={<IconFileText size={16} />}
                        withAsterisk
                        clearable
                        size="md"
                        styles={{
                          input: {
                            border: '2px dashed var(--mantine-color-blue-4)',
                            backgroundColor: 'var(--mantine-color-blue-0)',
                            '&:hover': {
                              borderColor: 'var(--mantine-color-blue-6)',
                              backgroundColor: 'var(--mantine-color-blue-1)',
                            }
                          }
                        }}
                      />
                    </div>

                    <Alert icon={<IconInfoCircle size={16} />} color="blue">
                      <Text size="sm">
                        <strong>File Requirements:</strong> Maximum 10MB file size, 50,000 URLs limit.
                        Each line should contain one valid URL.
                      </Text>
                    </Alert>

                    {form.values.url_source.urls.length > 0 && (
                      <Alert icon={<IconInfoCircle size={16} />} color="green">
                        <Text size="sm">
                          <strong>File loaded:</strong> {form.values.url_source.file_name} with {form.values.url_source.urls.length} URLs
                        </Text>
                      </Alert>
                    )}
                  </>
                )}


                {/* Content Extraction Settings - Common for all modes */}
                <Divider label={<Text size="xs" c="dimmed">Content Extraction Settings</Text>} labelPosition="center" />

                <NumberInput
                  label="Crawl Depth"
                  placeholder="4"
                  min={0}
                  max={6}
                  step={1}
                  clampBehavior="strict"
                  description="Maximum depth for crawling (0 = single page only)"
                  {...form.getInputProps('crawl_depth')}
                />
              </Stack>
            </Card>
          )}

          {/* Local Files Configuration Section */}
          {form.values.content_source_type === 'local_files' && (
            <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
              <Stack gap="md">
                <Group gap="xs" align="center">
                  <IconFileText size={18} color="var(--mantine-color-orange-6)" />
                  <Text size="sm" fw={600} c="orange">Local Files Configuration</Text>
                </Group>

                <Select
                  label="File Type"
                  placeholder="Select file type"
                  required
                  data={localFileModes}
                  description="Choose the type of files you want to upload"
                  {...form.getInputProps('scraping_mode')}
                />

                <div
                  onDragOver={handleDragOver}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDrop={handleLocalFilesDrop}
                >
                  <FileInput
                    label="Upload Files"
                    placeholder="Click to upload or drag and drop files"
                    multiple
                    accept=".html,.htm,.md,.markdown,.pdf,.docx,.txt"
                    description="Upload HTML, Markdown, PDF, DOCX, or TXT files to process (drag & drop supported)"
                    onChange={(files) => {
                      console.log('🚀 FileInput onChange called with:', files);
                      if (files) {
                        const fileList = Array.from(files);
                        console.log('🚀 Processing files:', fileList.map(f => ({ name: f.name, type: f.type, size: f.size })));

                        // Store actual File objects for upload
                        setUploadedFiles(fileList);

                        // Create metadata for form display
                        const localFiles = fileList.map((file, index) => ({
                          file_id: `file_${Date.now()}_${index}`,
                          original_filename: file.name,
                          file_path: '', // Will be set after upload
                          file_type: file.name.split('.').pop()?.toLowerCase() || 'html',
                          file_size: file.size,
                          upload_timestamp: new Date().toISOString(),
                        }));
                        console.log('🚀 Setting local_files to:', localFiles);
                        console.log('🚀 Setting file_types to:', [...new Set(localFiles.map(f => f.file_type))]);
                        form.setFieldValue('local_files', localFiles);
                        form.setFieldValue('file_types', [...new Set(localFiles.map(f => f.file_type))]);

                        // DON'T override scraping_mode - user already selected it via dropdown
                        // The scraping_mode dropdown is already set to the file type

                        // Set output format based on file types
                        const fileTypes = [...new Set(localFiles.map(f => f.file_type))];
                        if (fileTypes.includes('html') || fileTypes.includes('htm')) {
                          // HTML files can have html, markdown, or llm_markdown output
                          form.setFieldValue('output_format', 'html');
                        } else {
                          // All other file types (markdown, pdf, docx, txt) use markdown output
                          form.setFieldValue('output_format', 'markdown');
                        }
                      } else {
                        console.log('🚀 No files provided to onChange');
                      }
                    }}
                    styles={{
                      input: {
                        border: '2px dashed var(--mantine-color-blue-4)',
                        backgroundColor: 'var(--mantine-color-blue-0)',
                        '&:hover': {
                          borderColor: 'var(--mantine-color-blue-6)',
                          backgroundColor: 'var(--mantine-color-blue-1)',
                        }
                      }
                    }}
                  />
                </div>

                {form.values.local_files && form.values.local_files.length > 0 && (
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" fw={500}>Uploaded Files:</Text>
                      <Text size="xs" c="dimmed">{form.values.local_files.length} files</Text>
                    </Group>
                    <ScrollArea h={300} type="scroll">
                      <Stack gap="xs">
                        {form.values.local_files.map((file: any, index: number) => (
                          <Group key={index} justify="space-between" p="xs" style={{ backgroundColor: 'var(--mantine-color-gray-1)', borderRadius: '4px' }}>
                            <Text size="sm">{file.original_filename}</Text>
                            <Text size="xs" c="dimmed">{(file.file_size / 1024).toFixed(1)} KB</Text>
                          </Group>
                        ))}
                      </Stack>
                    </ScrollArea>
                  </Stack>
                )}
              </Stack>
            </Card>
          )}

          {/* Confluence Configuration Section */}
          {form.values.content_source_type === 'confluence' && (
            <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
              <Stack gap="md">
                <Group gap="xs" align="center">
                  <IconBook size={18} color="var(--mantine-color-cyan-6)" />
                  <Text size="sm" fw={600} c="cyan">Confluence Configuration</Text>
                </Group>

                {/* Credential Selection */}
                <Select
                  label="Confluence Credential"
                  placeholder="Select existing credential or create new"
                  required
                  clearable
                  searchable
                  data={confluenceCredentials?.map((cred: any) => ({
                    value: cred.id,
                    label: cred.name,
                    description: `${cred.cloud_url} (${cred.username_or_email})`
                  })) || []}
                  description="Select a previously created Confluence credential"
                  {...form.getInputProps('confluence_credential_id')}
                />

                {/* Confluence Extraction Mode */}
                <Select
                  label="Extraction Mode"
                  placeholder="Select extraction mode"
                  required
                  data={confluenceModes.map(mode => ({
                    value: mode.value,
                    label: mode.label,
                    description: mode.description
                  }))}
                  description={
                    confluenceModes.find(m => m.value === form.values.confluence_mode)?.description || 'Select a mode'
                  }
                  {...form.getInputProps('confluence_mode')}
                />

                {/* Mode-specific fields */}
                {form.values.confluence_mode === 'space_pages' && (
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Confluence Spaces</Text>
                    <Text size="xs" c="dimmed">Enter space keys to extract pages from (e.g., TECH, DOCS)</Text>
                    {form.values.confluence_config.space_keys.map((key, index) => (
                      <Group key={index} mb="xs">
                        <TextInput
                          value={key}
                          onChange={(e) => {
                            const newKeys = [...form.values.confluence_config.space_keys];
                            newKeys[index] = e.target.value;
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              space_keys: newKeys
                            });
                          }}
                          placeholder="Enter space key"
                          style={{ flex: 1 }}
                        />
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          type="button"
                          onClick={() => {
                            const newKeys = form.values.confluence_config.space_keys.filter((_, i) => i !== index);
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              space_keys: newKeys
                            });
                          }}
                        >
                          <IconX size={14} />
                        </ActionIcon>
                      </Group>
                    ))}
                    <Button
                      variant="light"
                      leftSection={<IconPlus size={16} />}
                      type="button"
                      onClick={() => {
                        form.setFieldValue('confluence_config', {
                          ...form.values.confluence_config,
                          space_keys: [...form.values.confluence_config.space_keys, '']
                        });
                      }}
                      fullWidth
                      size="sm"
                    >
                      Add Space
                    </Button>
                  </Stack>
                )}

                {form.values.confluence_mode === 'specific_pages' && (
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Page IDs</Text>
                    <Text size="xs" c="dimmed">Enter Confluence page IDs to extract</Text>
                    {form.values.confluence_config.page_ids.map((id, index) => (
                      <Group key={index} mb="xs">
                        <TextInput
                          value={id}
                          onChange={(e) => {
                            const newIds = [...form.values.confluence_config.page_ids];
                            newIds[index] = e.target.value;
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              page_ids: newIds
                            });
                          }}
                          placeholder="Enter page ID"
                          style={{ flex: 1 }}
                        />
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          type="button"
                          onClick={() => {
                            const newIds = form.values.confluence_config.page_ids.filter((_, i) => i !== index);
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              page_ids: newIds
                            });
                          }}
                        >
                          <IconX size={14} />
                        </ActionIcon>
                      </Group>
                    ))}
                    <Button
                      variant="light"
                      leftSection={<IconPlus size={16} />}
                      type="button"
                      onClick={() => {
                        form.setFieldValue('confluence_config', {
                          ...form.values.confluence_config,
                          page_ids: [...form.values.confluence_config.page_ids, '']
                        });
                      }}
                      fullWidth
                      size="sm"
                    >
                      Add Page ID
                    </Button>
                  </Stack>
                )}

                {form.values.confluence_mode === 'pages_with_label' && (
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Labels</Text>
                    <Text size="xs" c="dimmed">Enter labels to extract pages with</Text>
                    {form.values.confluence_config.labels.map((label, index) => (
                      <Group key={index} mb="xs">
                        <TextInput
                          value={label}
                          onChange={(e) => {
                            const newLabels = [...form.values.confluence_config.labels];
                            newLabels[index] = e.target.value;
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              labels: newLabels
                            });
                          }}
                          placeholder="Enter label"
                          style={{ flex: 1 }}
                        />
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          type="button"
                          onClick={() => {
                            const newLabels = form.values.confluence_config.labels.filter((_, i) => i !== index);
                            form.setFieldValue('confluence_config', {
                              ...form.values.confluence_config,
                              labels: newLabels
                            });
                          }}
                        >
                          <IconX size={14} />
                        </ActionIcon>
                      </Group>
                    ))}
                    <Button
                      variant="light"
                      leftSection={<IconPlus size={16} />}
                      type="button"
                      onClick={() => {
                        form.setFieldValue('confluence_config', {
                          ...form.values.confluence_config,
                          labels: [...form.values.confluence_config.labels, '']
                        });
                      }}
                      fullWidth
                      size="sm"
                    >
                      Add Label
                    </Button>
                  </Stack>
                )}

                {/* Optional settings */}
                <Divider label={<Text size="xs" c="dimmed">Optional Settings</Text>} labelPosition="center" />
                <Group grow>
                  <Switch
                    label="Include Attachments"
                    checked={form.values.confluence_config.include_attachments}
                    onChange={(e) => {
                      form.setFieldValue('confluence_config', {
                        ...form.values.confluence_config,
                        include_attachments: e.currentTarget.checked
                      });
                    }}
                  />
                  <Switch
                    label="Include Comments"
                    checked={form.values.confluence_config.include_comments}
                    onChange={(e) => {
                      form.setFieldValue('confluence_config', {
                        ...form.values.confluence_config,
                        include_comments: e.currentTarget.checked
                      });
                    }}
                  />
                </Group>
              </Stack>
            </Card>
          )}

        </Stack>
      );
    }

    // Step 2: Domain Filtering (only for web scraping)
    if (currentStepLabel === 'Domain Filtering') {
      return (
        <Stack gap="md">
          <Title order={4}>Domain & URL Filtering</Title>
          <Text c="dimmed">Configure which domains and URLs to include or exclude from scraping.</Text>

          <Group grow align="flex-start">
            <div style={{ flex: 1 }}>
              <Text size="sm" fw={500} mb="xs">Allowed Subdomains</Text>
              <Text size="xs" c="dimmed" mb="md">
                Add subdomains to allow for crawling. Leave empty to allow all subdomains.
              </Text>

              {form.values.allowed_subdomains.map((domain, index) => (
                <Group key={index} mb="xs">
                  <TextInput
                    value={domain}
                    onChange={(e) => {
                      const newDomains = [...form.values.allowed_subdomains];
                      newDomains[index] = e.target.value;
                      form.setFieldValue('allowed_subdomains', newDomains);
                    }}
                    placeholder="Enter subdomain"
                    style={{ flex: 1 }}
                  />
                  <ActionIcon
                    color="red"
                    variant="subtle"
                    size="sm"
                    type="button"
                    onClick={() => {
                      const newDomains = form.values.allowed_subdomains.filter((_, i) => i !== index);
                      form.setFieldValue('allowed_subdomains', newDomains);
                    }}
                  >
                    <IconX size={14} />
                  </ActionIcon>
                </Group>
              ))}

              <Button
                variant="light"
                leftSection={<IconPlus size={16} />}
                type="button"
                onClick={() => {
                  const newDomains = [...form.values.allowed_subdomains, ''];
                  form.setFieldValue('allowed_subdomains', newDomains);
                }}
                fullWidth
                size="sm"
              >
                Add Allowed Subdomain
              </Button>
            </div>

            <div style={{ flex: 1 }}>
              <Text size="sm" fw={500} mb="xs">Blocked Subdomains</Text>
              <Text size="xs" c="dimmed" mb="md">
                Add subdomains to block from crawling.
              </Text>

              {form.values.blocked_subdomains.map((domain, index) => (
                <Group key={index} mb="xs">
                  <TextInput
                    value={domain}
                    onChange={(e) => {
                      const newDomains = [...form.values.blocked_subdomains];
                      newDomains[index] = e.target.value;
                      form.setFieldValue('blocked_subdomains', newDomains);
                    }}
                    placeholder="Enter subdomain"
                    style={{ flex: 1 }}
                  />
                  <ActionIcon
                    color="red"
                    variant="subtle"
                    size="sm"
                    type="button"
                    onClick={() => {
                      const newDomains = form.values.blocked_subdomains.filter((_, i) => i !== index);
                      form.setFieldValue('blocked_subdomains', newDomains);
                    }}
                  >
                    <IconX size={14} />
                  </ActionIcon>
                </Group>
              ))}

              <Button
                variant="light"
                leftSection={<IconPlus size={16} />}
                type="button"
                onClick={() => {
                  const newDomains = [...form.values.blocked_subdomains, ''];
                  form.setFieldValue('blocked_subdomains', newDomains);
                }}
                fullWidth
                size="sm"
              >
                Add Blocked Subdomain
              </Button>
            </div>
          </Group>

          <div>
            <Text size="sm" fw={500} mb="xs">URL Patterns</Text>
            <Text size="xs" c="dimmed" mb="md">
              Add URL patterns to exclude from crawling. Use wildcards like * for matching.
            </Text>

            {form.values.url_patterns.map((pattern, index) => (
              <Card key={index} withBorder p="md" mb="sm">
                <Group justify="space-between" mb="xs">
                  <Text size="sm" fw={500}>Pattern {index + 1}</Text>
                  <ActionIcon
                    color="red"
                    variant="subtle"
                    size="sm"
                    type="button"
                    onClick={() => {
                      const newPatterns = form.values.url_patterns.filter((_, i) => i !== index);
                      form.setFieldValue('url_patterns', newPatterns);
                    }}
                  >
                    <IconX size={14} />
                  </ActionIcon>
                </Group>

                <Stack gap="sm">
                  <TextInput
                    label="URL Pattern"
                    placeholder="*/jp/*, */admin/*, */test*"
                    value={pattern.pattern}
                    onChange={(e) => {
                      const newPatterns = [...form.values.url_patterns];
                      newPatterns[index] = { ...pattern, pattern: e.target.value };
                      form.setFieldValue('url_patterns', newPatterns);
                    }}
                    description="Use * as wildcard. Example: */jp/* matches any URL containing /jp/"
                  />

                  <Switch
                    label="Exclude matching URLs"
                    description="When enabled, URLs matching this pattern will be excluded from crawling"
                    checked={pattern.reverse}
                    onChange={(e) => {
                      const newPatterns = [...form.values.url_patterns];
                      newPatterns[index] = { ...pattern, reverse: e.currentTarget.checked };
                      form.setFieldValue('url_patterns', newPatterns);
                    }}
                  />
                </Stack>
              </Card>
            ))}

            <Button
              variant="light"
              leftSection={<IconPlus size={16} />}
              type="button"
              onClick={() => {
                const newPatterns = [...form.values.url_patterns, { pattern: '', reverse: true }];
                form.setFieldValue('url_patterns', newPatterns);
              }}
              fullWidth
            >
              Add URL Pattern
            </Button>
          </div>

          <Alert icon={<IconInfoCircle size={16} />} color="blue">
            <Text size="sm">
              <strong>URL Patterns:</strong> Use patterns like "*/jp/*" to exclude Japanese translations,
              "*/admin/*" to exclude admin pages, etc. Set "reverse: true" to exclude matching URLs.
            </Text>
          </Alert>
        </Stack>
      );
    }

    // Step 3: Content Filter (only for web scraping or HTML files)
    if (currentStepLabel === 'Content Filter') {
      return (
        <Stack gap="md">
          <Title order={4}>Content Filter</Title>
          <Text c="dimmed">
            Configure content extraction and filtering options.
          </Text>

          {/* Target Elements Section - Creative Layout */}
          <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
            <Stack gap="md">
              {/* Header with Icon */}
              <Group gap="xs" mb="sm">
                <IconCode size={20} color="var(--mantine-color-blue-6)" />
                <Text size="sm" fw={600} c="blue">Target Elements</Text>
                <Badge size="sm" color="blue" variant="light">
                  {form.values.target_elements.length} selectors
                </Badge>
              </Group>

              {/* Testing Parameters Display */}
              <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                <Stack gap="xs">
                  <Text size="sm" fw={500} c="blue">Testing Parameters</Text>
                  <Stack gap="xs">
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">URL:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                        {form.values.url || 'Not set'}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Selectors:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.target_elements.length > 0
                          ? form.values.target_elements.join(', ')
                          : 'None selected'
                        }
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Output Format:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.output_format || 'html'}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Crawl Depth:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.crawl_depth || 0}
                      </Text>
                    </Group>
                  </Stack>
                </Stack>
              </Card>

              {/* Main Content - Two Column Layout */}
              <Group align="flex-start" gap="lg" style={{ position: 'relative' }}>
                {/* Left Side - Input and Selectors */}
                <Stack style={{ flex: 1 }} gap="md">
                  {/* Add Selector Section */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'white' }}>
                    <Stack gap="sm">
                      <Group gap="xs" align="center">
                        <IconPlus size={16} color="var(--mantine-color-green-6)" />
                        <Text size="sm" fw={500} c="green">Add New Selector</Text>
                      </Group>

                      <Group gap="xs" align="flex-end">
                        <TextInput
                          placeholder="Enter CSS selector (e.g., 'body > div.container > main > article')"
                          value={newSelector}
                          onChange={(e) => setNewSelector(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && newSelector.trim()) {
                              const currentElements = form.values.target_elements;
                              if (!currentElements.includes(newSelector.trim())) {
                                form.setFieldValue('target_elements', [...currentElements, newSelector.trim()]);
                                setNewSelector('');
                              }
                            }
                          }}
                          style={{ flex: 1 }}
                          size="sm"
                        />
                        <Button
                          size="sm"
                          color="green"
                          variant="light"
                          onClick={() => {
                            if (newSelector.trim()) {
                              const currentElements = form.values.target_elements;
                              if (!currentElements.includes(newSelector.trim())) {
                                form.setFieldValue('target_elements', [...currentElements, newSelector.trim()]);
                                setNewSelector('');
                              }
                            }
                          }}
                          disabled={!newSelector.trim()}
                          leftSection={<IconPlus size={14} />}
                        >
                          Add
                        </Button>
                      </Group>
                      <Text size="xs" c="dimmed">💡 Press Enter or click Add to add the selector</Text>
                    </Stack>
                  </Card>

                  {/* Current Selectors */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'white' }}>
                    <Stack gap="sm">
                      <Group gap="xs" align="center">
                        <IconFileText size={16} color="var(--mantine-color-blue-6)" />
                        <Text size="sm" fw={500} c="blue">Current Selectors</Text>
                      </Group>

                      <Stack gap="xs">
                        {/* User selectors */}
                        {form.values.target_elements.map((selector, index) => (
                          <Group key={index} justify="space-between" p="sm" style={{
                            backgroundColor: 'var(--mantine-color-gray-0)',
                            borderRadius: 'var(--mantine-radius-sm)',
                            border: '1px solid var(--mantine-color-gray-3)'
                          }}>
                            <Group gap="xs">
                              <Badge size="xs" color="gray" variant="light">{index + 1}</Badge>
                              <Text size="sm" style={{ fontFamily: 'monospace' }}>{selector}</Text>
                            </Group>
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="red"
                              onClick={() => {
                                const newElements = form.values.target_elements.filter((_, i) => i !== index);
                                form.setFieldValue('target_elements', newElements);
                              }}
                            >
                              <IconX size={14} />
                            </ActionIcon>
                          </Group>
                        ))}

                        {form.values.target_elements.length === 0 && (
                          <Text size="sm" c="dimmed" p="md" style={{ textAlign: 'center', fontStyle: 'italic' }}>
                            No additional selectors added yet
                          </Text>
                        )}
                      </Stack>
                    </Stack>
                  </Card>
                </Stack>

                {/* Right Side - Help and Tips */}
                <Stack style={{ flex: 0, minWidth: '40%' }} gap="md">
                  {/* Quick Start Guide */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <IconInfoCircle size={16} color="var(--mantine-color-blue-6)" />
                        <Text size="sm" fw={500} c="blue">Quick Start Guide</Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        Define which HTML elements to extract content from. Use browser dev tools to get precise selectors.
                      </Text>
                    </Stack>
                  </Card>

                  {/* Browser Dev Tools Steps */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-cyan-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <Text size="sm" fw={500} c="cyan">🔧 How to Get Selectors</Text>
                      </Group>
                      <Stack gap="xs">
                        <Text size="xs" c="dimmed">1. Open your target page in browser</Text>
                        <Text size="xs" c="dimmed">2. Right-click element → "Inspect"</Text>
                        <Text size="xs" c="dimmed">3. Right-click in Dev Tools → "Copy selector"</Text>
                        <Text size="xs" c="dimmed">4. Paste here</Text>
                      </Stack>
                    </Stack>
                  </Card>


                  {/* Header Note */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <Text size="sm" fw={500} c="blue">📋 Header Metadata</Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        The &lt;head&gt; section (title, meta tags, etc.) is automatically scraped.
                        You only need to specify content elements here.
                      </Text>
                    </Stack>
                  </Card>
                </Stack>
              </Group>

              {/* Floating Test Section */}
              {(form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) && (
                <div style={{
                  position: 'absolute',
                  top: '20px',
                  right: '10px',
                  zIndex: 100,
                  minWidth: isContentFilterTestVisible ? '400px' : '200px'
                }}>
                  {!isContentFilterTestVisible ? (
                    // Collapsed state - show toggle button
                    <Button
                      onClick={() => setIsContentFilterTestVisible(true)}
                      leftSection={<IconWand size={16} />}
                      color="cyan"
                      variant="filled"
                      size="sm"
                      style={{
                        height: '36px',
                        fontSize: '12px',
                        whiteSpace: 'nowrap',
                        padding: '0 8px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                      }}
                    >
                      Test Selectors
                    </Button>
                  ) : (
                    // Expanded state - show full test section
                    <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-cyan-0)', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
                      <Stack gap="md">
                        <Group gap="xs" align="center" justify="space-between">
                          <Group gap="xs" align="center">
                            <IconWand size={18} color="var(--mantine-color-cyan-6)" />
                            <Text size="sm" fw={600} c="cyan">Test Selectors</Text>
                          </Group>
                          <Button
                            variant="subtle"
                            size="xs"
                            onClick={() => setIsContentFilterTestVisible(false)}
                            leftSection={<IconChevronRight size={14} />}
                            color="cyan"
                          >
                            Hide
                          </Button>
                        </Group>

                        {/* Test Parameters Display */}
                        <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                          <Stack gap="xs">
                            <Text size="sm" fw={500} c="blue">Testing Parameters</Text>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">URL:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                  {form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0 ? `${form.values.url_source.urls[0]} (first of ${form.values.url_source.urls.length})` : 'Not set')}
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Selectors:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {form.values.target_elements.length > 0
                                    ? form.values.target_elements.join(', ')
                                    : 'None selected'
                                  }
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Output Format:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {testOutputFormat}
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Crawl Depth:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {form.values.crawl_depth || 0}
                                </Text>
                              </Group>
                            </Stack>
                          </Stack>
                        </Card>

                        {/* Test Controls */}
                        <Stack gap="sm">
                          <Select
                            label="Test Output Format"
                            placeholder="Select output format"
                            value={testOutputFormat}
                            onChange={(value) => setTestOutputFormat(value as 'html' | 'markdown')}
                            data={[
                              { value: 'html', label: 'HTML' },
                              { value: 'markdown', label: 'Markdown' }
                            ]}
                            description="Choose the output format for testing"
                          />
                          <Button
                            onClick={handleTestSelectors}
                            loading={isTesting}
                            disabled={(!form.values.url && !(form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) || form.values.target_elements.length === 0}
                            leftSection={<IconWand size={16} />}
                            color="cyan"
                            variant="filled"
                            fullWidth
                          >
                            Test Selectors
                          </Button>
                        </Stack>

                        {testResult && (
                          <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                            <Stack gap="xs">
                              <Group justify="space-between">
                                <Group gap="xs">
                                  <Button
                                    size="xs"
                                    variant="light"
                                    onClick={handleCopyResult}
                                    leftSection={<IconCopy size={12} />}
                                  >
                                    Copy
                                  </Button>
                                  <Button
                                    size="xs"
                                    variant="light"
                                    onClick={() => setTestResult(null)}
                                  >
                                    Clear
                                  </Button>
                                </Group>
                              </Group>
                              <ScrollArea.Autosize mah={200}>
                                <Text
                                  size="xs"
                                  style={{
                                    fontFamily: 'monospace',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                  }}
                                >
                                  {testResult}
                                </Text>
                              </ScrollArea.Autosize>
                            </Stack>
                          </Card>
                        )}
                      </Stack>
                    </Card>
                  )}
                </div>
              )}

            </Stack>
          </Card>

        </Stack>
      );
    }

    // Step 3: Content Filter (only for web scraping or HTML files)
    if (currentStepLabel === 'Content Filter') {
      return (
        <Stack gap="md">
          <Title order={4}>Content Filter</Title>
          <Text c="dimmed">
            Configure content extraction and filtering options.
          </Text>

          {/* Target Elements Section - Creative Layout */}
          <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
            <Stack gap="md">
              {/* Header with Icon */}
              <Group gap="xs" mb="sm">
                <IconCode size={20} color="var(--mantine-color-blue-6)" />
                <Text size="sm" fw={600} c="blue">Target Elements</Text>
                <Badge size="sm" color="blue" variant="light">
                  {form.values.target_elements.length} selectors
                </Badge>
              </Group>

              {/* Testing Parameters Display */}
              <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                <Stack gap="xs">
                  <Text size="sm" fw={500} c="blue">Testing Parameters</Text>
                  <Stack gap="xs">
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">URL:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                        {form.values.url || 'Not set'}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Selectors:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.target_elements.length > 0
                          ? form.values.target_elements.join(', ')
                          : 'None selected'
                        }
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Output Format:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.output_format || 'html'}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Text size="xs" c="dimmed">Crawl Depth:</Text>
                      <Text size="xs" style={{ fontFamily: 'monospace' }}>
                        {form.values.crawl_depth || 0}
                      </Text>
                    </Group>
                  </Stack>
                </Stack>
              </Card>

              {/* Main Content - Two Column Layout */}
              <Group align="flex-start" gap="lg" style={{ position: 'relative' }}>
                {/* Left Side - Input and Selectors */}
                <Stack style={{ flex: 1 }} gap="md">
                  {/* Add Selector Section */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'white' }}>
                    <Stack gap="sm">
                      <Group gap="xs" align="center">
                        <IconPlus size={16} color="var(--mantine-color-green-6)" />
                        <Text size="sm" fw={500} c="green">Add New Selector</Text>
                      </Group>

                      <Group gap="xs" align="flex-end">
                        <TextInput
                          placeholder="Enter CSS selector (e.g., 'body > div.container > main > article')"
                          value={newSelector}
                          onChange={(e) => setNewSelector(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && newSelector.trim()) {
                              const currentElements = form.values.target_elements;
                              if (!currentElements.includes(newSelector.trim())) {
                                form.setFieldValue('target_elements', [...currentElements, newSelector.trim()]);
                                setNewSelector('');
                              }
                            }
                          }}
                          style={{ flex: 1 }}
                          size="sm"
                        />
                        <Button
                          size="sm"
                          color="green"
                          variant="light"
                          onClick={() => {
                            if (newSelector.trim()) {
                              const currentElements = form.values.target_elements;
                              if (!currentElements.includes(newSelector.trim())) {
                                form.setFieldValue('target_elements', [...currentElements, newSelector.trim()]);
                                setNewSelector('');
                              }
                            }
                          }}
                          disabled={!newSelector.trim()}
                          leftSection={<IconPlus size={14} />}
                        >
                          Add
                        </Button>
                      </Group>
                      <Text size="xs" c="dimmed">💡 Press Enter or click Add to add the selector</Text>
                    </Stack>
                  </Card>

                  {/* Current Selectors */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'white' }}>
                    <Stack gap="sm">
                      <Group gap="xs" align="center">
                        <IconFileText size={16} color="var(--mantine-color-blue-6)" />
                        <Text size="sm" fw={500} c="blue">Current Selectors</Text>
                      </Group>

                      <Stack gap="xs">
                        {/* User selectors */}
                        {form.values.target_elements.map((selector, index) => (
                          <Group key={index} justify="space-between" p="sm" style={{
                            backgroundColor: 'var(--mantine-color-gray-0)',
                            borderRadius: 'var(--mantine-radius-sm)',
                            border: '1px solid var(--mantine-color-gray-3)'
                          }}>
                            <Group gap="xs">
                              <Badge size="xs" color="gray" variant="light">{index + 1}</Badge>
                              <Text size="sm" style={{ fontFamily: 'monospace' }}>{selector}</Text>
                            </Group>
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="red"
                              onClick={() => {
                                const newElements = form.values.target_elements.filter((_, i) => i !== index);
                                form.setFieldValue('target_elements', newElements);
                              }}
                            >
                              <IconX size={14} />
                            </ActionIcon>
                          </Group>
                        ))}

                        {form.values.target_elements.length === 0 && (
                          <Text size="sm" c="dimmed" p="md" style={{ textAlign: 'center', fontStyle: 'italic' }}>
                            No additional selectors added yet
                          </Text>
                        )}
                      </Stack>
                    </Stack>
                  </Card>
                </Stack>

                {/* Right Side - Help and Tips */}
                <Stack style={{ flex: 0, minWidth: '40%' }} gap="md">
                  {/* Quick Start Guide */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <IconInfoCircle size={16} color="var(--mantine-color-blue-6)" />
                        <Text size="sm" fw={500} c="blue">Quick Start Guide</Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        Define which HTML elements to extract content from. Use browser dev tools to get precise selectors.
                      </Text>
                    </Stack>
                  </Card>

                  {/* Browser Dev Tools Steps */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-cyan-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <Text size="sm" fw={500} c="cyan">🔧 How to Get Selectors</Text>
                      </Group>
                      <Stack gap="xs">
                        <Text size="xs" c="dimmed">1. Open your target page in browser</Text>
                        <Text size="xs" c="dimmed">2. Right-click element → "Inspect"</Text>
                        <Text size="xs" c="dimmed">3. Right-click in Dev Tools → "Copy selector"</Text>
                        <Text size="xs" c="dimmed">4. Paste here</Text>
                      </Stack>
                    </Stack>
                  </Card>

                  {/* Header Note */}
                  <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Stack gap="xs">
                      <Group gap="xs" align="center">
                        <Text size="sm" fw={500} c="blue">📋 Header Metadata</Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        The &lt;head&gt; section (title, meta tags, etc.) is automatically scraped.
                        You only need to specify content elements here.
                      </Text>
                    </Stack>
                  </Card>
                </Stack>
              </Group>

              {/* Floating Test Section */}
              {(form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) && (
                <div style={{
                  position: 'absolute',
                  top: '20px',
                  right: '10px',
                  zIndex: 100,
                  minWidth: isContentFilterTestVisible ? '400px' : '200px'
                }}>
                  {!isContentFilterTestVisible ? (
                    // Collapsed state - show toggle button
                    <Button
                      onClick={() => setIsContentFilterTestVisible(true)}
                      leftSection={<IconWand size={16} />}
                      color="cyan"
                      variant="filled"
                      size="sm"
                      style={{
                        height: '36px',
                        fontSize: '12px',
                        whiteSpace: 'nowrap',
                        padding: '0 8px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                      }}
                    >
                      Test Selectors
                    </Button>
                  ) : (
                    // Expanded state - show full test section
                    <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-cyan-0)', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
                      <Stack gap="md">
                        <Group gap="xs" align="center" justify="space-between">
                          <Group gap="xs" align="center">
                            <IconWand size={18} color="var(--mantine-color-cyan-6)" />
                            <Text size="sm" fw={600} c="cyan">Test Selectors</Text>
                          </Group>
                          <Button
                            variant="subtle"
                            size="xs"
                            onClick={() => setIsContentFilterTestVisible(false)}
                            leftSection={<IconChevronRight size={14} />}
                            color="cyan"
                          >
                            Hide
                          </Button>
                        </Group>

                        {/* Test Parameters Display */}
                        <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                          <Stack gap="xs">
                            <Text size="sm" fw={500} c="blue">Testing Parameters</Text>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">URL:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                  {form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0 ? `${form.values.url_source.urls[0]} (first of ${form.values.url_source.urls.length})` : 'Not set')}
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Selectors:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {form.values.target_elements.length > 0
                                    ? form.values.target_elements.join(', ')
                                    : 'None selected'
                                  }
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Output Format:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {testOutputFormat}
                                </Text>
                              </Group>
                              <Group gap="xs">
                                <Text size="xs" c="dimmed">Crawl Depth:</Text>
                                <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                  {form.values.crawl_depth || 0}
                                </Text>
                              </Group>
                            </Stack>
                          </Stack>
                        </Card>

                        {/* Test Controls */}
                        <Stack gap="sm">
                          <Select
                            label="Test Output Format"
                            placeholder="Select output format"
                            value={testOutputFormat}
                            onChange={(value) => setTestOutputFormat(value as 'html' | 'markdown')}
                            data={[
                              { value: 'html', label: 'HTML' },
                              { value: 'markdown', label: 'Markdown' }
                            ]}
                            description="Choose the output format for testing"
                          />
                          <Button
                            onClick={handleTestSelectors}
                            loading={isTesting}
                            disabled={(!form.values.url && !(form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) || form.values.target_elements.length === 0}
                            leftSection={<IconWand size={16} />}
                            color="cyan"
                            variant="filled"
                            fullWidth
                          >
                            Test Selectors
                          </Button>
                        </Stack>

                        {testResult && (
                          <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                            <Stack gap="xs">
                              <Group justify="space-between">
                                <Group gap="xs">
                                  <Button
                                    size="xs"
                                    variant="light"
                                    onClick={handleCopyResult}
                                    leftSection={<IconCopy size={12} />}
                                  >
                                    Copy
                                  </Button>
                                  <Button
                                    size="xs"
                                    variant="light"
                                    onClick={() => setTestResult(null)}
                                  >
                                    Clear
                                  </Button>
                                </Group>
                              </Group>
                              <ScrollArea.Autosize mah={200}>
                                <Text
                                  size="xs"
                                  style={{
                                    fontFamily: 'monospace',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                  }}
                                >
                                  {testResult}
                                </Text>
                              </ScrollArea.Autosize>
                            </Stack>
                          </Card>
                        )}
                      </Stack>
                    </Card>
                  )}
                </div>
              )}
            </Stack>
          </Card>
        </Stack>
      );
    }

    // Step 4: Generation (only for web scraping, Confluence, HTML, PDF, DOCX, TXT)
    if (currentStepLabel === 'Generation') {
      return (
        <Stack gap="md">
          <Title order={4}>Generation</Title>
          <Text c="dimmed">
            Configure output format and content processing options.
          </Text>

          {/* Generation Step Container with Relative Positioning */}
          <div style={{ position: 'relative' }}>
            {/* Testing Recommendations */}
            <Alert icon={<IconInfoCircle />} color="blue" variant="light">
              <Stack gap="sm">
                <Text size="sm" fw={600}>🧪 Test Your Configuration Before Running</Text>
                <Text size="sm">
                  <strong>Important:</strong> We strongly recommend testing your content extraction and processing settings before running the job.
                </Text>
                <Text size="sm">
                  Once the job runs and creates vectors, you cannot modify the content without rerunning the entire job and recreating all vectors.
                </Text>
                <Text size="sm" c="dimmed">
                  💡 Test your configuration right here with the tester below.
                </Text>
              </Stack>
            </Alert>

            {/* Main Content Layout */}
            <Group align="flex-start" gap="lg">
              {/* Left Side - Configuration Options */}
              <Stack style={{ flex: 1 }} gap="md">

                {/* Output Format Selection */}
                <Stack gap="sm">
                  <Text size="sm" fw={500}>Output Format</Text>
                  <Radio.Group
                    value={form.values.output_format}
                    onChange={(value) => form.setFieldValue('output_format', value as 'html' | 'markdown')}
                  >
                    <Group gap="lg">
                      <Radio
                        value="html"
                        label={
                          <Group gap="xs">
                            <IconCode size={16} />
                            <div>
                              <Text size="sm" fw={500}>Raw HTML</Text>
                              <Text size="xs" c="dimmed">Extract raw HTML content as-is</Text>
                            </div>
                          </Group>
                        }
                      />
                      <Radio
                        value="markdown"
                        label={
                          <Group gap="xs">
                            <IconFileText size={16} />
                            <div>
                              <Text size="sm" fw={500}>Markdown</Text>
                              <Text size="xs" c="dimmed">Convert content to structured markdown</Text>
                            </div>
                          </Group>
                        }
                      />
                    </Group>
                  </Radio.Group>
                </Stack>

                {/* Markdown Generation Options */}
                {form.values.output_format === 'markdown' && (
                  <Stack gap="sm">
                    <Text size="sm" fw={500}>Markdown Generation Method</Text>
                    <Radio.Group
                      value={form.values.markdown_generation}
                      onChange={(value) => form.setFieldValue('markdown_generation', value as 'standard' | 'llm')}
                    >
                      <Stack gap="sm">
                        <Radio
                          value="standard"
                          label={
                            <div>
                              <Text size="sm" fw={500}>Standard Markdown</Text>
                              <Text size="xs" c="dimmed">Uses content filter threshold for processing</Text>
                            </div>
                          }
                        />
                        <Radio
                          value="llm"
                          label={
                            <div>
                              <Text size="sm" fw={500}>LLM-Powered Markdown</Text>
                              <Text size="xs" c="dimmed">Uses AI to intelligently convert and structure content</Text>
                            </div>
                          }
                        />
                      </Stack>
                    </Radio.Group>
                  </Stack>
                )}

                {/* Content Filter Threshold - only show for standard markdown */}
                {form.values.output_format === 'markdown' && form.values.markdown_generation === 'standard' && (
                  <NumberInput
                    label="Content Filter Threshold"
                    placeholder="0.5"
                    min={0}
                    max={1}
                    step={0.1}
                    decimalScale={1}
                    description="Threshold for content filtering (0.0 to 1.0). Lower → more content retained, higher → more content pruned"
                    {...form.getInputProps('content_filter_threshold')}
                  />
                )}

                {/* LLM Content Filter - only show for LLM markdown */}
                {form.values.output_format === 'markdown' && form.values.markdown_generation === 'llm' && (
                  <>
                    <Alert icon={<IconInfoCircle />} color="yellow" title="Cost Notice">
                      <Text size="sm">
                        <strong>Note:</strong> Using LLM Content Filters will incur additional costs as each crawled page
                        will be processed by an LLM to extract and shape the content based on your filtering criteria.
                        The cost depends on the model used and the number of pages crawled.
                      </Text>
                    </Alert>

                    {filtersLoading ? (
                      <Center p="xl">
                        <Loader />
                      </Center>
                    ) : (
                      <>
                        <Select
                          label="LLM Content Filter"
                          placeholder="None (skip filtering)"
                          description="Select a filter configuration to apply during crawling"
                          data={[
                            { value: '', label: 'None' },
                            ...(contentFilters || []).map((filter: any) => ({
                              value: filter.id,
                              label: filter.name,
                            })),
                          ]}
                          value={form.values.llm_content_filter_id || ''}
                          onChange={(value) => form.setFieldValue('llm_content_filter_id', value || null)}
                          clearable
                        />

                        {form.values.llm_content_filter_id && (
                          <Alert icon={<IconInfoCircle />} color="blue" variant="light">
                            <Stack gap="xs">
                              <Text size="sm">
                                <strong>What are Content Filters?</strong>
                              </Text>
                              <Text size="sm" mt="xs">
                                Content filters use AI to extract only relevant content from crawled pages,
                                removing navigation elements, ads, footers, and other noise. This improves
                                the quality of your knowledge base.
                              </Text>
                            </Stack>
                          </Alert>
                        )}

                        <Button
                          variant="light"
                          leftSection={<IconPlus />}
                          onClick={() => setCreateFilterModalOpened(true)}
                        >
                          Create New Filter
                        </Button>
                      </>
                    )}
                  </>
                )}
              </Stack>

            </Group>

            {/* Floating Preview Content Button - Within Generation Step */}
            {form.values.url && (
              <div style={{
                position: 'absolute',
                top: '20px',
                right: '0px',
                zIndex: 10,
                minWidth: isTestSectionVisible ? '400px' : '200px'
              }}>
                {!isTestSectionVisible ? (
                  // Collapsed state - show toggle button
                  <Button
                    onClick={() => setIsTestSectionVisible(true)}
                    leftSection={<IconWand size={16} />}
                    color="cyan"
                    variant="filled"
                    size="sm"
                    style={{
                      height: '36px',
                      fontSize: '12px',
                      whiteSpace: 'nowrap',
                      padding: '0 8px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                    }}
                  >
                    Preview Content
                  </Button>
                ) : (
                  // Expanded state - show full test section
                  <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-cyan-0)', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
                    <Stack gap="md">
                      <Group gap="xs" align="center" justify="space-between">
                        <Group gap="xs" align="center">
                          <IconWand size={18} color="var(--mantine-color-cyan-6)" />
                          <Text size="sm" fw={600} c="cyan">Preview Content</Text>
                        </Group>
                        <Button
                          variant="subtle"
                          size="xs"
                          onClick={() => setIsTestSectionVisible(false)}
                          leftSection={<IconChevronRight size={14} />}
                          color="cyan"
                        >
                          Hide
                        </Button>
                      </Group>

                      {/* Configuration Preview */}
                      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                        <Stack gap="xs">
                          <Text size="sm" fw={500}>Current Configuration:</Text>
                          <Text size="xs">
                            <strong>Output Format:</strong> {form.values.output_format}
                          </Text>
                          {form.values.output_format === 'markdown' && (
                            <>
                              <Text size="xs">
                                <strong>Generation Method:</strong> {form.values.markdown_generation}
                              </Text>
                              {form.values.markdown_generation === 'standard' && (
                                <Text size="xs">
                                  <strong>Threshold:</strong> {form.values.content_filter_threshold}
                                </Text>
                              )}
                              {form.values.markdown_generation === 'llm' && form.values.llm_content_filter_id && (
                                <Text size="xs">
                                  <strong>LLM Filter:</strong> {form.values.llm_content_filter_id}
                                </Text>
                              )}
                            </>
                          )}
                        </Stack>
                      </Alert>

                      {/* Test Controls */}
                      <Stack gap="sm">
                        <Button
                          onClick={handleTestGeneration}
                          loading={isTesting}
                          disabled={(!form.values.url && !(form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) || form.values.target_elements.length === 0}
                          leftSection={<IconWand size={16} />}
                          color="cyan"
                          variant="filled"
                          fullWidth
                        >
                          Preview Content
                        </Button>
                        <Text size="xs" c="dimmed" ta="center">
                          Test with your current configuration
                        </Text>
                      </Stack>

                      {testResult && (
                        <Card withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                          <Stack gap="xs">
                            <Group justify="flex-end">
                              <Button
                                size="xs"
                                variant="light"
                                onClick={() => setTestResult(null)}
                              >
                                Clear
                              </Button>
                            </Group>
                            <ScrollArea.Autosize mah={200}>
                              <Text
                                size="xs"
                                style={{
                                  fontFamily: 'monospace',
                                  whiteSpace: 'pre-wrap',
                                  wordBreak: 'break-word'
                                }}
                              >
                                {testResult}
                              </Text>
                            </ScrollArea.Autosize>
                          </Stack>
                        </Card>
                      )}
                    </Stack>
                  </Card>
                )}
              </div>
            )}

          </div>
        </Stack>
      );
    }

    // Step 5: Review (always last)
    if (currentStepLabel === 'Review') {
      return (
        <Stack gap="md">
          <Title order={4}>Review Configuration</Title>
          <Text c="dimmed">Review your configuration before creating it.</Text>

          <Card withBorder>
            <Stack gap="md">
              <Group>
                <Text fw={500}>Name:</Text>
                <Text>{form.values.name}</Text>
              </Group>

              <Group>
                <Text fw={500}>Description:</Text>
                <Text>{form.values.description}</Text>
              </Group>

              <Group>
                <Text fw={500}>Scraping Mode:</Text>
                <Text>{form.values.scraping_mode}</Text>
              </Group>

              {form.values.scraping_mode === 'single_page' && (
                <Group>
                  <Text fw={500}>Page URL:</Text>
                  <Text>{form.values.url}</Text>
                </Group>
              )}

              {form.values.scraping_mode === 'multiple_pages' && (
                <>
                  {form.values.content_source_type === 'web_scraping' ? (
                    <>
                      <Group>
                        <Text fw={500}>File Name:</Text>
                        <Text>{form.values.url_source.file_name}</Text>
                      </Group>
                      <Group>
                        <Text fw={500}>URLs Count:</Text>
                        <Text>{form.values.url_source.urls.length}</Text>
                      </Group>
                    </>
                  ) : (
                    <>
                      <Group>
                        <Text fw={500}>Files Uploaded:</Text>
                        <Text>{form.values.local_files?.length || 0} files</Text>
                      </Group>
                      <Group>
                        <Text fw={500}>Total Size:</Text>
                        <Text>
                          {((form.values.local_files?.reduce((sum: number, file: any) => sum + (file.file_size || 0), 0) || 0) / 1024 / 1024).toFixed(2)} MB
                        </Text>
                      </Group>
                    </>
                  )}
                </>
              )}

              {form.values.scraping_mode === 'website' && (
                <Group>
                  <Text fw={500}>Website URL:</Text>
                  <Text>{form.values.url}</Text>
                </Group>
              )}

              {form.values.scraping_mode === 'website' && (
                <Group>
                  <Text fw={500}>Crawl Depth:</Text>
                  <Text>{form.values.crawl_depth}</Text>
                </Group>
              )}

              {/* Only show web scraping fields for web scraping */}
              {form.values.content_source_type === 'web_scraping' && (
                <>
                  <Group>
                    <Text fw={500}>Target Elements:</Text>
                    <Text>{form.values.target_elements.join(', ')}</Text>
                  </Group>

                  <Group>
                    <Text fw={500}>Content Filter Threshold:</Text>
                    <Text>{form.values.content_filter_threshold}</Text>
                  </Group>
                </>
              )}

              {form.values.allowed_subdomains.length > 0 && (
                <Group>
                  <Text fw={500}>Allowed Subdomains:</Text>
                  <Text>{form.values.allowed_subdomains.join(', ')}</Text>
                </Group>
              )}

              {form.values.blocked_subdomains.length > 0 && (
                <Group>
                  <Text fw={500}>Blocked Subdomains:</Text>
                  <Text>{form.values.blocked_subdomains.join(', ')}</Text>
                </Group>
              )}

              {form.values.url_patterns.length > 0 && (
                <div>
                  <Text fw={500} mb="xs">URL Patterns:</Text>
                  {form.values.url_patterns.map((pattern, index) => (
                    <Group key={index} mb="xs" pl="md">
                      <Text size="sm" c="dimmed">•</Text>
                      <Text size="sm" fw={500}>{pattern.pattern}</Text>
                      <Text size="sm" c={pattern.reverse ? "red" : "green"}>
                        ({pattern.reverse ? "Exclude" : "Include"})
                      </Text>
                    </Group>
                  ))}
                </div>
              )}

              <Divider />

              {/* Only show Content Filter for web scraping */}
              {form.values.content_source_type === 'web_scraping' && (
                <Group>
                  <Text fw={500}>Content Filter:</Text>
                  <Text>
                    {form.values.llm_content_filter_id ? (
                      (() => {
                        const filter = contentFilters?.find((f: any) => f.id === form.values.llm_content_filter_id);
                        return filter ? filter.name : 'Unknown Filter';
                      })()
                    ) : (
                      <span style={{ color: 'var(--mantine-color-dimmed)' }}>None</span>
                    )}
                  </Text>
                </Group>
              )}

              {/* Confluence Configuration Summary */}
              {form.values.content_source_type === 'confluence' && (
                <>
                  <Divider />
                  <Group>
                    <Text fw={500}>Confluence Credential:</Text>
                    <Text>
                      {confluenceCredentials?.find((c: any) => c.id === form.values.confluence_credential_id)?.name || 'Not selected'}
                    </Text>
                  </Group>

                  <Group>
                    <Text fw={500}>Extraction Mode:</Text>
                    <Text>{form.values.confluence_mode}</Text>
                  </Group>

                  {form.values.confluence_mode === 'space_pages' && form.values.confluence_config.space_keys.length > 0 && (
                    <Group>
                      <Text fw={500}>Spaces:</Text>
                      <Text>{form.values.confluence_config.space_keys.join(', ')}</Text>
                    </Group>
                  )}

                  {form.values.confluence_mode === 'specific_pages' && form.values.confluence_config.page_ids.length > 0 && (
                    <Group>
                      <Text fw={500}>Pages:</Text>
                      <Text>{form.values.confluence_config.page_ids.join(', ')}</Text>
                    </Group>
                  )}

                  {form.values.confluence_mode === 'pages_with_label' && form.values.confluence_config.labels.length > 0 && (
                    <Group>
                      <Text fw={500}>Labels:</Text>
                      <Text>{form.values.confluence_config.labels.join(', ')}</Text>
                    </Group>
                  )}

                  {(form.values.confluence_config.include_attachments || form.values.confluence_config.include_comments) && (
                    <Stack gap="xs">
                      {form.values.confluence_config.include_attachments && (
                        <Group>
                          <Text fw={500}>Include Attachments:</Text>
                          <Badge color="blue" size="sm">Yes</Badge>
                        </Group>
                      )}
                      {form.values.confluence_config.include_comments && (
                        <Group>
                          <Text fw={500}>Include Comments:</Text>
                          <Badge color="blue" size="sm">Yes</Badge>
                        </Group>
                      )}
                    </Stack>
                  )}
                </>
              )}

            </Stack>
          </Card>

          <Alert icon={<IconInfoCircle size={16} />} color="green">
            <Text size="sm">
              <strong>Ready to create!</strong> Click "Create Configuration" to save your knowledge source configuration.
            </Text>
          </Alert>
        </Stack>
      );
    }

    // If no matching step label, return null (shouldn't happen)
    console.warn('Unknown step label:', currentStepLabel);
    return null;
  };

  return (
    <Page title="Create RAG Configuration">
      <PageHeader
        title="Create RAG Configuration"
        breadcrumbs={breadcrumbs}
      />

      <Group justify="space-between" mb="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          component={Link}
          to={paths.dashboard.management.knowledgeSources.configs}
        >
          Back to Crawling Sources Config
        </Button>
        <div />
      </Group>

      <form
        onSubmit={(e) => {
          console.log('🚨 FORM onSubmit TRIGGERED!', { activeStep, totalSteps: stepConfigs.length, isFormValid: isFormValid(), hasReachedFinalStep, isSubmitting });
          e.preventDefault();
          e.stopPropagation();

          // CRITICAL: Prevent double submission
          if (isSubmitting) {
            console.log('⛔ BLOCKED: Already submitting!');
            return;
          }

          // Only allow submission on the final step and only if form is valid AND user has explicitly reached the final step
          const isFinalStep = activeStep === stepConfigs.length - 1;
          if (isFinalStep && isFormValid() && hasReachedFinalStep) {
            console.log('✅ Allowing form submission', { activeStep, finalStepIndex: stepConfigs.length - 1 });
            form.onSubmit(handleSubmit)(e);
          } else {
            console.log('❌ Blocking form submission', {
              activeStep,
              finalStepIndex: stepConfigs.length - 1,
              isFinalStep,
              isFormValid: isFormValid(),
              hasReachedFinalStep,
              reason: !isFinalStep ? 'Not on final step' : !hasReachedFinalStep ? 'Not explicitly reached final step' : 'Form not valid'
            });
          }
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && activeStep < stepConfigs.length - 1) {
            e.preventDefault();
          }
        }}
      >
        <Stack gap="md">
          <ColorfulVerticalStepper
            activeStep={activeStep}
            completedSteps={completedSteps}
            steps={stepConfigs}
            onStepClick={handleStepClick}
          >
            {renderStepContent()}
          </ColorfulVerticalStepper>

          <Group justify="space-between">
            <Button
              variant="subtle"
              component={Link}
              to={paths.dashboard.management.knowledgeSources.configs}
            >
              Cancel
            </Button>

            <Group>
              {activeStep > 0 && (
                <Button type="button" variant="default" onClick={prevStep}>
                  Previous
                </Button>
              )}

              {activeStep < stepConfigs.length - 1 ? (
                <Button
                  type="button"
                  onClick={(e) => {
                    console.log('🔄 Next button clicked', { activeStep, totalSteps: stepConfigs.length, validateStep: validateStep(activeStep) });
                    e.preventDefault();
                    e.stopPropagation();
                    nextStep();
                  }}
                  disabled={!validateStep(activeStep)}
                >
                  Next
                </Button>
              ) : (
                <Button
                  type="submit"
                  loading={isSubmitting}
                  disabled={!isFormValid() || isSubmitting}
                  onClick={(e) => {
                    console.log('🔄 Create Configuration button clicked', { activeStep, totalSteps: stepConfigs.length, isSubmitting });
                    // Prevent any action if already submitting
                    if (isSubmitting) {
                      console.log('⛔ BLOCKED: Button click ignored - already submitting');
                      e.preventDefault();
                      e.stopPropagation();
                      return;
                    }
                    setHasReachedFinalStep(true);
                  }}
                >
                  Create Configuration
                </Button>
              )}
            </Group>
          </Group>
        </Stack>
      </form>

      {/* Create Content Filter Modal */}
      <Modal
        opened={createFilterModalOpened}
        onClose={() => {
          setCreateFilterModalOpened(false);
          filterForm.reset();
        }}
        title={
          <Group gap="sm">
            <IconFilter size={20} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="sm">Create Content Filter</Text>
          </Group>
        }
        centered
        size="xl"
        radius="md"
        shadow="xl"
        transitionProps={{
          transition: 'slide-up',
          duration: 300,
          timingFunction: 'ease-out',
        }}
        overlayProps={{
          backgroundOpacity: 0.55,
          blur: 3,
          transitionProps: {
            transition: 'fade',
            duration: 300,
            timingFunction: 'ease-in-out',
          },
        }}
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-blue-0)',
            borderBottom: '1px solid var(--mantine-color-blue-2)',
            paddingBottom: '16px',
            marginBottom: '16px',
          },
          body: {
            maxHeight: '85vh',
            overflowY: 'auto',
          },
        }}
      >
        <form onSubmit={filterForm.onSubmit(handleCreateFilter)}>
          <Stack gap="md">
            <Alert icon={<IconInfoCircle />} color="yellow">
              <Text size="sm">
                <strong>Cost Notice:</strong> Using LLM Content Filters will process each crawled page through an LLM,
                incurring additional API costs based on the model and page count.
              </Text>
            </Alert>

            <TextInput
              label="Filter Name"
              placeholder="e.g., Documentation Content Filter"
              required
              {...filterForm.getInputProps('name')}
            />

            <Textarea
              label="Description"
              placeholder="Describe what this filter does (optional)"
              minRows={2}
              {...filterForm.getInputProps('description')}
            />

            <Divider label={<Text size="xs" c="dimmed">LLM Configuration</Text>} labelPosition="center" />

            {!providersLoading && generativeProviders.length === 0 && (
              <Alert icon={<IconInfoCircle />} color="orange" title="No LLM Providers Available">
                <Text size="sm">
                  You need to configure at least one LLM provider with generative capabilities before creating content filters.
                  Please go to <strong>Model Providers</strong> management to add one.
                </Text>
              </Alert>
            )}

            <Select
              label="LLM Provider"
              placeholder={generativeProviders.length === 0 ? "No providers available" : "Select a provider"}
              required
              description="Only active LLM providers with generative capabilities are shown"
              data={generativeProviders.map((provider: any) => ({
                value: provider.id,
                label: provider.name,
              }))}
              {...filterForm.getInputProps('llm_provider_id')}
              disabled={providersLoading || generativeProviders.length === 0}
              searchable
            />

            {filterForm.values.llm_provider_id && (
              <Select
                label="Model Name"
                placeholder="Select a model"
                required
                data={(() => {
                  const provider = generativeProviders?.find((p: any) => p.id === filterForm.values.llm_provider_id);
                  return provider?.generative?.models?.map((model: string) => ({
                    value: model,
                    label: model,
                  })) || [];
                })()}
                {...filterForm.getInputProps('llm_model_name')}
                searchable
              />
            )}

            <Divider label={<Text size="xs" c="dimmed">Advanced Settings</Text>} labelPosition="center" />

            <Group grow>
              <NumberInput
                label="Temperature"
                placeholder="0.0"
                min={0}
                max={2}
                step={0.1}
                decimalScale={1}
                description="LLM temperature (0 = deterministic)"
                {...filterForm.getInputProps('temperature')}
              />

              <NumberInput
                label="Max Retries"
                placeholder="3"
                min={1}
                max={10}
                description="Maximum number of API retries"
                {...filterForm.getInputProps('max_retries')}
              />

              <NumberInput
                label="Timeout (seconds)"
                placeholder="30"
                min={10}
                max={300}
                description="API call timeout"
                {...filterForm.getInputProps('timeout_seconds')}
              />
            </Group>

            <Divider label={<Text size="xs" c="dimmed">Filtering Instructions</Text>} labelPosition="center" />

            <Stack gap="md">
              <Text size="sm" c="dimmed">
                Choose a template or write custom instructions for content filtering:
              </Text>

              <Select
                label="Instruction Template"
                placeholder="Select a template or choose 'Custom' to write your own"
                data={[
                  { value: 'technical-docs', label: 'Technical Documentation' },
                  { value: 'api-reference', label: 'API Reference & Guides' },
                  { value: 'tutorial-content', label: 'Tutorials & How-to Guides' },
                  { value: 'release-notes', label: 'Release Notes & Changelogs' },
                  { value: 'troubleshooting', label: 'Troubleshooting & FAQ' },
                  { value: 'custom', label: 'Custom Instructions' }
                ]}
                onChange={(value) => {
                  if (value && value !== 'custom') {
                    const templates = {
                      'technical-docs': `# Technical Documentation Extraction

## Objective
Extract all relevant technical documentation content while preserving markdown structure.

## Content to Include

### Headers and Structure
- All headings and subheadings (H1, H2, H3, etc.)
- Maintain hierarchical structure
- Preserve header relationships

### Technical Content
- Paragraphs with technical information
- Code examples and snippets
- Configuration details
- API documentation
- Step-by-step instructions
- Troubleshooting information
- Feature descriptions
- Requirements and prerequisites

## Formatting Requirements
- Keep the content structure intact
- Preserve markdown formatting
- Maintain header hierarchy
- Use proper markdown syntax

## Content to Exclude
- Navigation elements
- Advertisements
- Unrelated content
- Footer information
- Sidebar content`,
                      'api-reference': `# API Reference Extraction

## Objective
Extract API reference documentation and guides with proper markdown structure.

## Content to Include

### API Documentation
- API endpoints and methods
- Request/response schemas
- Code examples and snippets
- Authentication details
- Rate limiting information
- Error codes and responses

### Structure Requirements
- Maintain header hierarchy
- Preserve markdown formatting
- Use proper code block syntax

## Content to Exclude
- Navigation elements
- Marketing content
- User comments
- Unrelated documentation`,
                      'tutorial-content': `# Tutorial Content Extraction

## Objective
Extract tutorial and how-to guide content with clear markdown structure.

## Content to Include

### Tutorial Elements
- Step-by-step instructions
- Code examples and snippets
- Screenshots descriptions
- Prerequisites and setup
- Troubleshooting tips
- Best practices

### Structure Requirements
- Maintain sequential order
- Preserve markdown formatting
- Use proper header hierarchy
- Include code blocks with syntax highlighting

## Content to Exclude
- Navigation menus
- Sidebar content
- Footer information
- Advertisement content`,
                      'release-notes': `# Release Notes Extraction

## Objective
Extract release notes and changelog content with proper markdown structure.

## Content to Include

### Version Information
- Version information
- New features and enhancements
- Bug fixes and improvements
- Breaking changes
- Migration guides
- Deprecation notices

### Structure Requirements
- Maintain chronological order
- Preserve markdown formatting
- Use proper header hierarchy
- Include version tags and dates

## Content to Exclude
- Navigation elements
- Marketing content
- Unrelated documentation`,
                      'troubleshooting': `# Troubleshooting Content Extraction

## Objective
Extract troubleshooting and FAQ content with clear markdown structure.

## Content to Include

### Problem-Solution Pairs
- Common issues and solutions
- Error messages and fixes
- Configuration problems
- Performance issues
- Compatibility notes
- Workarounds

### Structure Requirements
- Maintain Q&A format
- Preserve markdown formatting
- Use proper header hierarchy
- Include code examples for solutions

## Content to Exclude
- Navigation elements
- Marketing content
- Unrelated documentation`
                    };
                    filterForm.setFieldValue('instruction', templates[value as keyof typeof templates]);
                  }
                }}
              />

              <Textarea
                label="Filtering Instructions"
                placeholder="Tell the LLM what to extract and what to exclude"
                required
                minRows={10}
                maxRows={20}
                autosize
                description="Provide clear instructions for the LLM on how to filter content. The field will expand as you type."
                {...filterForm.getInputProps('instruction')}
              />
            </Stack>

            <Group justify="flex-end" mt="md">
              <Button
                variant="default"
                onClick={() => {
                  setCreateFilterModalOpened(false);
                  filterForm.reset();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" loading={isCreatingFilter}>
                Create Filter
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

    </Page>
  );
}
