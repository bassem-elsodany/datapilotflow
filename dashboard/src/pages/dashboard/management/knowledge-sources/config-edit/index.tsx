import { useCreateContentFilter, useGetContentFilters } from '@/api/resources/content-filters';
import { useGetKnowledgeSourceConfig, useGetUrlSourceConfig, useUpdateKnowledgeSourceConfig, useTestConfluenceCredentials } from '@/api/resources/knowledge-sources';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { ColorfulVerticalStepper, StepConfig } from '@/components/colorful-vertical-stepper';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { useTestCssSelectors } from '@/hooks/use-knowledge-source-test';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  CopyButton,
  Divider,
  FileInput,
  Group,
  List,
  Loader,
  Modal,
  NumberInput,
  Radio,
  ScrollArea,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
  IconBook,
  IconCheck,
  IconChevronRight,
  IconClipboardCheck,
  IconCode,
  IconCopy,
  IconExternalLink,
  IconEye,
  IconFileText,
  IconFilter,
  IconInfoCircle,
  IconLink,
  IconPlus,
  IconSettings,
  IconUpload,
  IconWand,
  IconWorld,
  IconX
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Edit Configuration' },
];


export default function EditKnowledgeSourceConfig() {
  const { configId } = useParams<{ configId: string }>();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [cssSelectorParts, setCssSelectorParts] = useState<Array<{ element: string; selector: string }>>([]);
  const [urlsModalOpen, setUrlsModalOpen] = useState(false);
  const [createFilterModalOpened, setCreateFilterModalOpened] = useState(false);
  const [newSelector, setNewSelector] = useState('');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isTestSectionVisible, setIsTestSectionVisible] = useState(false);
  const [isContentFilterTestVisible, setIsContentFilterTestVisible] = useState(false);
  const [testOutputFormat, setTestOutputFormat] = useState<'html' | 'markdown'>('html');
  const [newUploadedFiles, setNewUploadedFiles] = useState<File[]>([]);
  const [confluenceTestResult, setConfluenceTestResult] = useState<{ success: boolean; message: string; spaces?: any[] } | null>(null);
  const [isTestingConfluenceCredentials, setIsTestingConfluenceCredentials] = useState(false);
  const [availableSpaces, setAvailableSpaces] = useState<any[]>([]);

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

  const { data: config, isLoading, error } = useGetKnowledgeSourceConfig(configId!);
  const { data: urlSourceData, isLoading: urlSourceLoading } = useGetUrlSourceConfig(
    configId || '',
    config?.url_source_id || '',
    { enabled: !!configId && !!config?.url_source_id }
  );
  const { data: contentFilters, isLoading: filtersLoading, refetch: refetchFilters } = useGetContentFilters();
  const { data: allProviders, isLoading: providersLoading } = useGetActiveModelProviders();
  const createFilterMutation = useCreateContentFilter();
  const updateConfigMutation = useUpdateKnowledgeSourceConfig();
  const testSelectorsMutation = useTestCssSelectors();
  const testConfluenceCredentialsMutation = useTestConfluenceCredentials();

  // Filter for generative providers
  const generativeProviders = allProviders?.filter((provider: any) =>
    provider.generative !== null && provider.generative !== undefined
  ) || [];

  const filterForm = useForm({
    initialValues: {
      name: '',
      description: '',
      llm_provider_id: '',
      llm_model_name: '',
      temperature: 0.1,
      max_retries: 3,
      timeout_seconds: 30,
      instruction: '',
      enabled: true,
      verbose_logging: false,
      chunk_token_threshold: 1000
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      llm_provider_id: (value) => (!value ? 'LLM Provider is required' : null),
      llm_model_name: (value) => (!value ? 'Model is required' : null),
      instruction: (value) => (!value ? 'Filtering instructions are required' : null),
    },
  });

  const form = useForm({
    initialValues: {
      name: '',
      description: '',
      content_source_type: 'web_scraping' as 'web_scraping' | 'local_files' | 'confluence',
      url: '',
      scraping_mode: 'website' as 'single_page' | 'multiple_pages' | 'website' | 'html_files' | 'markdown_files' | 'pdf_files' | 'docx_files' | 'txt_files',
      url_source: {
        file_name: '',
        urls: [] as string[]
      },
      allowed_subdomains: [] as string[],
      blocked_subdomains: [] as string[],
      url_patterns: [] as Array<{ pattern: string; reverse: boolean }>,
      crawl_depth: 4,
      target_elements: [],
      content_filter_threshold: 0.6,
      llm_content_filter_id: null as string | null,
      output_format: 'html' as 'html' | 'markdown',
      markdown_generation: 'standard' as 'standard' | 'llm',
      local_files: [] as any[],
      file_types: [] as string[],
      confluence_config: {
        is_cloud_instance: true,
        cloud_url: '',
        username_or_email: '',
        api_token: '',
        space_keys: [] as string[],
        page_ids: [] as string[],
        labels: [] as string[],
        include_attachments: false,
        include_comments: false,
        expand_child_pages: false
      },
      new_llm_filter: null as {
        name: string;
        description: string;
        llm_provider_id: string;
        llm_model_name: string;
        temperature: number;
        max_retries: number;
        timeout_seconds: number;
        instruction: string;
        enabled: boolean;
        verbose_logging: boolean;
        chunk_token_threshold: number;
      } | null
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      url: (value) => (!value ? 'URL is required' : null),
    },
  });

  // Load existing configuration data
  useEffect(() => {
    if (config) {
      console.log('[ConfigEdit] Loading config data:', config);
      console.log('[ConfigEdit] URL from config:', config.url);
      console.log('[ConfigEdit] URL source data:', urlSourceData);

      // Initialize target elements
      setCssSelectorParts([]);

      const formValues = {
        name: config.name,
        description: config.description || '',
        content_source_type: config.content_source_type || 'web_scraping',
        url: config.url || '',
        scraping_mode: config.scraping_mode || 'website',
        url_source: {
          file_name: urlSourceData?.file_name || '',
          urls: urlSourceData?.urls || []
        },
        allowed_subdomains: config.allowed_subdomains || [],
        blocked_subdomains: config.blocked_subdomains || [],
        url_patterns: (config.url_patterns || []) as Array<{ pattern: string; reverse: boolean }>,
        crawl_depth: config.crawl_depth ?? 4,
        target_elements: config.target_elements || [],
        content_filter_threshold: config.content_filter_threshold || 0.6,
        output_format: config.output_format === 'llm_markdown' ? 'markdown' : (config.output_format || 'html'),
        markdown_generation: (config.output_format === 'llm_markdown' ? 'llm' : 'standard') as 'standard' | 'llm',
        llm_content_filter_id: config.llm_content_filter_id || null,
        local_files: config.local_files || [],
        file_types: config.file_types || [],
        confluence_config: {
          is_cloud_instance: (config as any).confluence_config?.is_cloud_instance ?? true,
          cloud_url: (config as any).confluence_config?.cloud_url || '',
          username_or_email: (config as any).confluence_config?.username_or_email || '',
          api_token: (config as any).confluence_config?.api_token || '',
          space_keys: (config as any).confluence_config?.space_keys || [],
          page_ids: (config as any).confluence_config?.page_ids || [],
          labels: (config as any).confluence_config?.labels || [],
          include_attachments: (config as any).confluence_config?.include_attachments ?? false,
          include_comments: (config as any).confluence_config?.include_comments ?? false,
          expand_child_pages: (config as any).confluence_config?.expand_child_pages ?? false
        },
        new_llm_filter: null as any
      };

      console.log('[ConfigEdit] Setting form values:', formValues);
      form.setValues(formValues as any);
    }
  }, [config, urlSourceData]);

  const parseCssSelector = (selector: string): Array<{ element: string; selector: string }> => {
    if (!selector) return [];

    const parts = selector.split(' > ');
    return parts.map(part => {
      const elementMatch = part.match(/^(\w+)/);
      const element = elementMatch ? elementMatch[1] : 'div';
      const selectorPart = part.replace(/^\w+/, '').trim();
      return { element, selector: selectorPart };
    });
  };

  const updateCssSelector = (parts: Array<{ element: string; selector: string }>) => {
    const selector = parts
      .map(part => {
        if (part.selector) {
          return `${part.element}${part.selector}`;
        }
        return part.element;
      })
      .join(' > ');

    // No longer needed with target_elements
  };

  const addCssSelectorPart = () => {
    const newParts = [...cssSelectorParts, { element: 'div', selector: '' }];
    updateCssSelector(newParts);
  };

  const removeCssSelectorPart = (index: number) => {
    const newParts = cssSelectorParts.filter((_, i) => i !== index);
    updateCssSelector(newParts);
  };

  const updateCssSelectorPart = (index: number, field: 'element' | 'selector', value: string) => {
    const newParts = [...cssSelectorParts];
    newParts[index] = { ...newParts[index], [field]: value };
    updateCssSelector(newParts);
  };

  const handleFileUpload = (file: File | null) => {
    if (!file) {
      form.setFieldValue('url_source', { file_name: '', urls: [] });
      return;
    }

    processFile(file);
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
    // Validate file type
    if (!file.name.endsWith('.txt')) {
      notifications.show({
        title: 'Invalid file type',
        message: 'Please upload a .txt file',
        color: 'red',
      });
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      notifications.show({
        title: 'File too large',
        message: 'File size must be less than 10MB',
        color: 'red',
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const urls = content
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && isValidUrl(line));

      // Validate URL count (50,000 limit)
      if (urls.length > 50000) {
        notifications.show({
          title: 'Too many URLs',
          message: 'File contains more than 50,000 URLs',
          color: 'red',
        });
        return;
      }

      console.log('[FileUpload] Parsed URLs:', urls.length, 'valid URLs from', file.name);
      console.log('[FileUpload] Sample URLs:', urls.slice(0, 5));

      form.setFieldValue('url_source', {
        file_name: file.name,
        urls: urls
      });

      console.log('[FileUpload] Form values after setFieldValue:', form.values.url_source);
      console.log('[FileUpload] Full form values:', form.values);
      console.log('[FileUpload] Scraping mode:', form.values.scraping_mode);
      console.log('[FileUpload] Validation result:', validateStep(1));

      notifications.show({
        title: 'File uploaded successfully',
        message: `Loaded ${urls.length} URLs from ${file.name}`,
        color: 'green',
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

  const addSubdomain = (type: 'allowed' | 'blocked') => {
    const field = type === 'allowed' ? 'allowed_subdomains' : 'blocked_subdomains';
    const current = form.values[field];
    form.setFieldValue(field, [...current, '']);
  };

  const removeSubdomain = (type: 'allowed' | 'blocked', index: number) => {
    const field = type === 'allowed' ? 'allowed_subdomains' : 'blocked_subdomains';
    const current = form.values[field];
    form.setFieldValue(field, current.filter((_, i) => i !== index));
  };

  const updateSubdomain = (type: 'allowed' | 'blocked', index: number, value: string) => {
    const field = type === 'allowed' ? 'allowed_subdomains' : 'blocked_subdomains';
    const current = form.values[field];
    const updated = [...current];
    updated[index] = value;
    form.setFieldValue(field, updated);
  };

  const addUrlPattern = () => {
    form.setFieldValue('url_patterns', [...form.values.url_patterns, { pattern: '', reverse: false }]);
  };

  const removeUrlPattern = (index: number) => {
    form.setFieldValue('url_patterns', form.values.url_patterns.filter((_, i) => i !== index));
  };

  const updateUrlPattern = (index: number, field: 'pattern' | 'reverse', value: string | boolean) => {
    const updated = [...form.values.url_patterns];
    updated[index] = { ...updated[index], [field]: value };
    form.setFieldValue('url_patterns', updated);
  };

  const validateStep = (step: number): boolean => {
    const currentStepLabel = stepConfigs[step]?.label;
    console.log('[ValidateStep] Step:', step, 'Label:', currentStepLabel);
    console.log('[ValidateStep] Form values:', form.values);

    if (!currentStepLabel) {
      console.warn('⚠️ No step config found for step', step);
      return false;
    }

    // Validate based on step label (not hardcoded index!)
    if (currentStepLabel?.includes('Basic Info')) {
      // Validate basic info
      const step0Valid = !!form.values.name;
      console.log('[ValidateStep] Basic Info - name:', form.values.name, 'valid:', step0Valid);

      // For local files mode, validate files
      if (form.values.content_source_type === 'local_files') {
        const hasExistingFiles = form.values.local_files && form.values.local_files.length > 0;
        const hasNewFiles = newUploadedFiles.length > 0;
        const filesValid = hasExistingFiles || hasNewFiles;
        console.log('[ValidateStep] local_files mode:', {
          hasExistingFiles,
          hasNewFiles,
          filesValid
        });
        return step0Valid && filesValid;
      }

      // For Confluence, check that credentials and mode are provided
      if (form.values.content_source_type === 'confluence') {
        if (!form.values.confluence_config?.cloud_url || !form.values.confluence_config?.username_or_email || !form.values.confluence_config?.api_token) {
          console.log('❌ Form invalid: Confluence credentials not complete');
          return false;
        }
        if (!form.values.scraping_mode) {
          console.log('❌ Form invalid: No scraping mode selected');
          return false;
        }
        console.log('✅ Confluence validation passed');
        return step0Valid;
      }

      // Validate scraping config for web scraping
      console.log('[ValidateStep] web_scraping - url:', form.values.url, 'scraping_mode:', form.values.scraping_mode);

      // For multiple_pages mode, URL is optional in edit mode
      if (form.values.scraping_mode === 'multiple_pages') {
        console.log('[ValidateStep] VALID (multiple_pages mode, URL optional)');
        return step0Valid;
      }

      // For single_page and website modes, URL is required
      if (!form.values.url) {
        console.log('[ValidateStep] INVALID: no URL');
        return false;
      }

      console.log('[ValidateStep] Basic Info - VALID');
      return step0Valid;
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

  // Step configurations with brand colors
  const getStepConfigs = (): StepConfig[] => {
    const isWebScraping = form.values.content_source_type === 'web_scraping';
    const isLocalFiles = form.values.content_source_type === 'local_files';
    const isConfluence = form.values.content_source_type === 'confluence';
    const scrapingMode = form.values.scraping_mode;

    // Step 1: Basic Info (always shown)
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
      description: 'Review and update',
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
    return configs;
  }, [form.values.content_source_type, form.values.scraping_mode]);

  const handleStepClick = (step: number) => {
    if (step < activeStep) {
      // Allow going back to any previous step
      setActiveStep(step);
    } else if (step === activeStep + 1) {
      // Allow going forward only if current step is valid
      if (validateStep(activeStep)) {
        setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
        setActiveStep(step);
      }
    } else if (step > activeStep + 1 && completedSteps.includes(step - 1)) {
      // Allow jumping to future steps if the previous step is completed
      setActiveStep(step);
    }
    // Allow free navigation between completed and current steps
  };

  const nextStep = () => {
    if (validateStep(activeStep)) {
      setCompletedSteps(prev => [...prev.filter(s => s !== activeStep), activeStep]);
      setActiveStep((current) => (current < stepConfigs.length - 1 ? current + 1 : current));
    }
  };

  const prevStep = () => {
    setActiveStep((current) => (current > 0 ? current - 1 : current));
  };

  // Test Confluence credentials
  const handleTestConfluenceCredentials = async () => {
    const { cloud_url, username_or_email, api_token } = form.values.confluence_config;

    if (!cloud_url || !username_or_email || !api_token) {
      notifications.show({
        title: 'Missing Credentials',
        message: 'Please fill in all Confluence credential fields',
        color: 'red',
      });
      return;
    }

    setIsTestingConfluenceCredentials(true);
    setConfluenceTestResult(null);

    try {
      const result = await testConfluenceCredentialsMutation.mutateAsync({
        cloud_url,
        username_or_email,
        api_token,
        is_cloud_instance: form.values.confluence_config.is_cloud_instance,
      });

      setConfluenceTestResult(result);

      if (result.success && result.spaces && result.spaces.length > 0) {
        setAvailableSpaces(result.spaces);
      }
    } catch (error) {
      console.error('Confluence credentials test failed:', error);
      setConfluenceTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to test credentials. Please check your credentials and try again.',
        spaces: []
      });
    } finally {
      setIsTestingConfluenceCredentials(false);
    }
  };

  const handleCreateFilter = (values: any) => {
    // Store the new filter data in the main form
    form.setFieldValue('new_llm_filter', values);
    form.setFieldValue('llm_content_filter_id', 'new'); // Mark as new filter

    notifications.show({
      title: 'Filter Added',
      message: `Content filter "${values.name}" will be created when you save the configuration.`,
      color: 'blue',
    });

    setCreateFilterModalOpened(false);
    filterForm.reset();
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

  // Drag and drop handler for local files upload in edit mode
  const handleLocalFilesDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    console.log('🚀 [EDIT MODE] handleLocalFilesDrop called with files:', files);
    if (files.length > 0) {
      console.log('🚀 [EDIT MODE] Processing dropped files:', files.map(f => ({ name: f.name, type: f.type, size: f.size })));

      // Add to new uploaded files
      const combinedFiles = [...newUploadedFiles, ...files];
      setNewUploadedFiles(combinedFiles);

      notifications.show({
        title: 'Files Ready',
        message: `${files.length} file(s) added and ready to upload`,
        color: 'blue'
      });

      console.log('🚀 [EDIT MODE] Total new files to upload:', combinedFiles.length);
    } else {
      console.log('🚀 [EDIT MODE] No files in drag&drop');
    }
  };

  const handleSubmit = async (values: typeof form.values) => {
    console.log('[HandleSubmit] Form submitted with values:', values);

    try {
      // Clean the data before sending
      const cleanedValues = { ...values };

      // Convert form values to correct output_format for database
      if (values.output_format === 'markdown' && values.markdown_generation === 'llm') {
        (cleanedValues as any).output_format = 'llm_markdown';
      } else if (values.output_format === 'markdown' && values.markdown_generation === 'standard') {
        (cleanedValues as any).output_format = 'markdown';
      } else {
        (cleanedValues as any).output_format = values.output_format; // 'html'
      }

      // Handle new LLM filter creation if needed
      if (values.new_llm_filter && values.llm_content_filter_id === 'new') {
        try {
          const newFilter = await createFilterMutation.mutateAsync({ variables: values.new_llm_filter as any });
          cleanedValues.llm_content_filter_id = newFilter.id;
          // Remove the new_llm_filter from cleanedValues
          const { new_llm_filter, ...restValues } = cleanedValues;
          Object.assign(cleanedValues, restValues);
        } catch (error) {
          notifications.show({
            title: 'Error',
            message: 'Failed to create LLM content filter. Please try again.',
            color: 'red',
          });
          return;
        }
      }

      console.log('[HandleSubmit] Scraping mode:', cleanedValues.scraping_mode);
      console.log('[HandleSubmit] URL source:', cleanedValues.url_source);
      console.log('[HandleSubmit] Config url_source_id:', config?.url_source_id);

      // Handle URL source for multiple_pages mode
      if (cleanedValues.scraping_mode !== 'multiple_pages' || cleanedValues.url_source.urls.length === 0) {
        console.log('[HandleSubmit] Removing url_source (not needed or empty)');
        delete (cleanedValues as any).url_source;
      } else {
        console.log('[HandleSubmit] Flattening url_source to urls and file_name');
        // Extract urls and file_name from url_source
        (cleanedValues as any).urls = cleanedValues.url_source.urls;
        (cleanedValues as any).file_name = cleanedValues.url_source.file_name || '';

        // Remove the url_source object
        delete (cleanedValues as any).url_source;

        console.log('[HandleSubmit] Added urls and file_name directly');
      }

      // Ensure target_elements is an array (no automatic additions)
      if (!cleanedValues.target_elements || !Array.isArray(cleanedValues.target_elements)) {
        cleanedValues.target_elements = [];
      }

      // Add Confluence specific fields
      if (cleanedValues.content_source_type === 'confluence') {
        (cleanedValues as any).confluence_config = {
          cloud_url: cleanedValues.confluence_config.cloud_url,
          username_or_email: cleanedValues.confluence_config.username_or_email,
          api_token: cleanedValues.confluence_config.api_token,
          space_keys: cleanedValues.confluence_config.space_keys.filter((k: string) => k.trim()),
          page_ids: cleanedValues.confluence_config.page_ids.filter((id: string) => id.trim()),
          labels: cleanedValues.confluence_config.labels.filter((l: string) => l.trim()),
          include_attachments: cleanedValues.confluence_config.include_attachments,
          include_comments: cleanedValues.confluence_config.include_comments,
          expand_child_pages: cleanedValues.confluence_config.expand_child_pages,
        };
        // Set scraping_mode at root level for Confluence
        (cleanedValues as any).scraping_mode = cleanedValues.scraping_mode;
        // Remove the is_cloud_instance as it's not part of the API schema, just used for UI
        delete (cleanedValues as any).confluence_config.is_cloud_instance;
      }

      // Remove any undefined or null values
      Object.keys(cleanedValues).forEach(key => {
        if (cleanedValues[key as keyof typeof cleanedValues] === undefined ||
          cleanedValues[key as keyof typeof cleanedValues] === null) {
          delete cleanedValues[key as keyof typeof cleanedValues];
        }
      });

      console.log('[HandleSubmit] Cleaned values to send:', cleanedValues);
      console.log('[HandleSubmit] URL source in cleaned values:', cleanedValues.url_source);
      if (cleanedValues.url_source) {
        console.log('[HandleSubmit] URL source URLs count:', cleanedValues.url_source.urls?.length);
        console.log('[HandleSubmit] URL source file name:', cleanedValues.url_source.file_name);
      }
      console.log('[HandleSubmit] New uploaded files count:', newUploadedFiles.length);
      console.log('[HandleSubmit] Calling mutation...');

      await updateConfigMutation.mutateAsync({
        configId: configId!,
        updateData: cleanedValues as any,
        files: newUploadedFiles.length > 0 ? newUploadedFiles : undefined
      });

      console.log('[HandleSubmit] Mutation successful!');

      notifications.show({
        title: 'Configuration updated',
        message: 'Knowledge source configuration has been updated successfully',
        color: 'green',
      });

      navigate(paths.dashboard.management.knowledgeSources.configs);
    } catch (error: any) {
      console.error('[HandleSubmit] Error:', error);
      notifications.show({
        title: 'Update failed',
        message: error.message || 'Failed to update configuration',
        color: 'red',
      });
    }
  };

  if (isLoading) {
    return (
      <Page title="Edit Configuration">
        <PageHeader title="Edit Configuration" breadcrumbs={breadcrumbs} />
        <Center py="xl">
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (error || !config) {
    return (
      <Page title="Edit Configuration">
        <PageHeader title="Edit Configuration" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error loading configuration">
          {error?.message || 'Configuration not found'}
        </Alert>
      </Page>
    );
  }

  return (
    <Page title="Edit Configuration">
      <PageHeader
        title="Edit Configuration"
        breadcrumbs={breadcrumbs}
      />

      <Group justify="space-between" mb="md">
        <Button
          variant="outline"
          leftSection={<IconArrowLeft size={16} />}
          component={Link}
          to={paths.dashboard.management.knowledgeSources.configs}
        >
          Back to Crawling Sources Config
        </Button>
      </Group>

      <form onSubmit={form.onSubmit(handleSubmit)}>
        <ColorfulVerticalStepper
          activeStep={activeStep}
          completedSteps={completedSteps}
          steps={stepConfigs}
          onStepClick={handleStepClick}
        >
          {/* Render based on step label, not hardcoded index */}
          {stepConfigs[activeStep]?.label?.includes('Basic Info') && (
            <Stack gap="md" mt="md">
              {/* Basic Information Section */}
              <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                <Stack gap="md">
                  <Group gap="xs" align="center">
                    <IconSettings size={18} color="var(--mantine-color-blue-6)" />
                    <Text size="lg" fw={600} c="blue">Basic Information</Text>
                  </Group>

                  <Select
                    label="Content Source Type"
                    value={form.values.content_source_type}
                    data={[
                      { value: 'web_scraping', label: 'Web Scraping' },
                      { value: 'local_files', label: 'Local Files' },
                      { value: 'confluence', label: 'Confluence' }
                    ]}
                    disabled
                    description="Cannot be changed after creation"
                  />

                  <TextInput
                    label="Configuration Name"
                    placeholder="Enter configuration name"
                    required
                    {...form.getInputProps('name')}
                  />

                  <Textarea
                    label="Description"
                    placeholder="Enter configuration description (optional)"
                    minRows={3}
                    {...form.getInputProps('description')}
                  />
                </Stack>
              </Card>

              {/* Web Scraping / Local Files Configuration Section */}
              {(form.values.content_source_type === 'web_scraping' || form.values.content_source_type === 'local_files') && (
              <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                <Stack gap="md">
                  <Group gap="xs" align="center">
                    <IconWorld size={18} color="var(--mantine-color-green-6)" />
                    <Text size="lg" fw={600} c="green">
                      {form.values.content_source_type === 'local_files' ? 'Local Files Configuration' : 'Web Scraping Configuration'}
                    </Text>
                  </Group>
                  {/* Compact Row: Scraping Mode and URL */}
                  <Group grow align="flex-start">
                    <Select
                      label={form.values.content_source_type === 'local_files' ? 'File Type' : 'Scraping Mode'}
                      placeholder={form.values.content_source_type === 'local_files' ? 'Select file type' : 'Select scraping mode'}
                      required
                      data={form.values.content_source_type === 'local_files' ? [
                        { value: 'html_files', label: 'HTML Files' },
                        { value: 'markdown_files', label: 'Markdown Files' },
                        { value: 'pdf_files', label: 'PDF Files' },
                        { value: 'docx_files', label: 'DOCX Files' },
                        { value: 'txt_files', label: 'TXT Files' }
                      ] : [
                        { value: 'single_page', label: 'Single Page' },
                        { value: 'multiple_pages', label: 'Multiple Pages (Upload URLs)' },
                        { value: 'website', label: 'Website Crawler' }
                      ]}
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
                        placeholder="https://example.com/page"
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
                    <Stack gap="md">
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
                          description={form.values.url_source.urls.length > 0
                            ? "Upload a new file to replace the existing URLs"
                            : "Upload a .txt file containing one URL per line (max 10MB, 50,000 URLs)"}
                          leftSection={<IconFileText size={16} />}
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

                      {urlSourceLoading && (
                        <Alert color="blue" variant="light">
                          <Group gap="xs">
                            <Loader size="xs" />
                            <Text size="sm">Loading existing URLs...</Text>
                          </Group>
                        </Alert>
                      )}

                      {form.values.url_source.urls.length > 0 && (
                        <Alert color="green" variant="light" icon={<IconCheck size={16} />}>
                          <Group justify="space-between" align="flex-start">
                            <Stack gap="xs" style={{ flex: 1 }}>
                              <Group gap="xs">
                                <Text size="sm" fw={600}>
                                  Currently loaded: {form.values.url_source.urls.length} URLs
                                </Text>
                                {form.values.url_source.file_name && (
                                  <Badge size="sm" variant="light" color="blue">
                                    {form.values.url_source.file_name}
                                  </Badge>
                                )}
                              </Group>
                              <Text size="xs" c="dimmed">
                                First few URLs: {form.values.url_source.urls.slice(0, 3).join(', ')}
                                {form.values.url_source.urls.length > 3 && '...'}
                              </Text>
                            </Stack>
                            <Button
                              size="xs"
                              variant="light"
                              leftSection={<IconEye size={14} />}
                              onClick={() => setUrlsModalOpen(true)}
                            >
                              View All
                            </Button>
                          </Group>
                        </Alert>
                      )}
                    </Stack>
                  )}

                  {/* Local Files Upload/Display */}
                  {form.values.content_source_type === 'local_files' && (
                    <Stack gap="md">
                      <Text size="sm" fw={500} c="dimmed">
                        Upload new files or manage existing ones
                      </Text>

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
                          accept={
                            form.values.scraping_mode === 'html_files' ? '.html,.htm' :
                              form.values.scraping_mode === 'markdown_files' ? '.md,.markdown' :
                                form.values.scraping_mode === 'pdf_files' ? '.pdf' :
                                  form.values.scraping_mode === 'docx_files' ? '.docx,.doc' :
                                    form.values.scraping_mode === 'txt_files' ? '.txt' : '*'
                          }
                          description="Upload additional files (drag & drop supported)"
                          leftSection={<IconUpload size={16} />}
                          value={newUploadedFiles}
                          onChange={(files) => {
                            if (files) {
                              const fileArray = Array.isArray(files) ? files : [files];
                              setNewUploadedFiles(fileArray);
                              notifications.show({
                                title: 'Files Ready',
                                message: `${fileArray.length} file(s) ready to upload`,
                                color: 'blue'
                              });
                            }
                          }}
                        />
                      </div>

                      {/* Show newly selected files */}
                      {newUploadedFiles.length > 0 && (
                        <Alert color="green" variant="light">
                          <Stack gap="xs">
                            <Group justify="space-between">
                              <Text size="sm" fw={600}>
                                New Files to Upload: {newUploadedFiles.length} file{newUploadedFiles.length !== 1 ? 's' : ''}
                              </Text>
                              <Button
                                size="xs"
                                variant="light"
                                color="red"
                                onClick={() => {
                                  setNewUploadedFiles([]);
                                  notifications.show({
                                    title: 'Cleared',
                                    message: 'New files cleared',
                                    color: 'orange'
                                  });
                                }}
                              >
                                Clear All
                              </Button>
                            </Group>
                            <Stack gap="xs">
                              {newUploadedFiles.map((file: File, index: number) => (
                                <Group key={index} gap="xs" justify="space-between">
                                  <Group gap="xs" style={{ flex: 1 }}>
                                    <IconFileText size={14} />
                                    <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                      {file.name}
                                    </Text>
                                    <Badge size="xs" variant="light" color="green">
                                      {(file.size / 1024).toFixed(2)} KB
                                    </Badge>
                                  </Group>
                                  <ActionIcon
                                    size="sm"
                                    color="red"
                                    variant="light"
                                    onClick={() => {
                                      const updatedFiles = newUploadedFiles.filter((_, i) => i !== index);
                                      setNewUploadedFiles(updatedFiles);
                                      notifications.show({
                                        title: 'File Removed',
                                        message: `${file.name} removed`,
                                        color: 'orange'
                                      });
                                    }}
                                    title="Remove file"
                                  >
                                    <IconX size={14} />
                                  </ActionIcon>
                                </Group>
                              ))}
                            </Stack>
                          </Stack>
                        </Alert>
                      )}

                      {form.values.local_files && form.values.local_files.length > 0 && (
                        <Alert color="blue" variant="light">
                          <Stack gap="xs">
                            <Text size="sm" fw={600}>
                              Currently Uploaded: {form.values.local_files.length} file{form.values.local_files.length !== 1 ? 's' : ''}
                            </Text>
                            <Stack gap="xs">
                              {form.values.local_files.map((file: any, index: number) => (
                                <Group key={file.file_id || index} gap="xs" justify="space-between">
                                  <Group gap="xs" style={{ flex: 1 }}>
                                    <IconFileText size={14} />
                                    <Text size="xs" style={{ fontFamily: 'monospace' }}>
                                      {file.original_filename}
                                    </Text>
                                    <Badge size="xs" variant="light">
                                      {(file.file_size / 1024).toFixed(2)} KB
                                    </Badge>
                                  </Group>
                                  <ActionIcon
                                    size="sm"
                                    color="red"
                                    variant="light"
                                    onClick={() => {
                                      const updatedFiles = form.values.local_files.filter((_: any, i: number) => i !== index);
                                      form.setFieldValue('local_files', updatedFiles);
                                      notifications.show({
                                        title: 'File Removed',
                                        message: `${file.original_filename} will be removed when you save`,
                                        color: 'orange'
                                      });
                                    }}
                                    title="Remove file"
                                  >
                                    <IconX size={14} />
                                  </ActionIcon>
                                </Group>
                              ))}
                            </Stack>
                          </Stack>
                        </Alert>
                      )}
                    </Stack>
                  )}

                  {form.values.content_source_type === 'web_scraping' && (
                    <>
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
                    </>
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

                    {/* Confluence Type Toggle */}
                    <Group justify="space-between" align="center">
                      <Stack gap="xs" style={{ flex: 1 }}>
                        <Text size="sm" fw={500}>Confluence Type</Text>
                        <Group gap="sm">
                          <Button
                            variant={form.values.confluence_config.is_cloud_instance !== false ? "filled" : "light"}
                            color="cyan"
                            size="sm"
                            onClick={() => form.setFieldValue('confluence_config.is_cloud_instance', true)}
                          >
                            Atlassian Cloud
                          </Button>
                          <Button
                            variant={form.values.confluence_config.is_cloud_instance === false ? "filled" : "light"}
                            color="cyan"
                            size="sm"
                            onClick={() => form.setFieldValue('confluence_config.is_cloud_instance', false)}
                          >
                            Local / Self-Hosted
                          </Button>
                        </Group>
                        <Text size="xs" c="dimmed">
                          {form.values.confluence_config.is_cloud_instance !== false
                            ? "Uses Atlassian Cloud API (atlassian.net URLs)"
                            : "Uses Server/Data Center API (localhost, self-hosted)"}
                        </Text>
                      </Stack>
                    </Group>

                    {/* Confluence Credentials */}
                    <Stack gap="xs">
                      <Text size="sm" fw={500}>Confluence Connection Details</Text>
                      <TextInput
                        label="URL"
                        placeholder={form.values.confluence_config.is_cloud_instance !== false ? "https://company.atlassian.net/wiki" : "http://localhost:8090"}
                        required
                        {...form.getInputProps('confluence_config.cloud_url')}
                        description={form.values.confluence_config.is_cloud_instance !== false
                          ? "Your Atlassian Cloud Confluence URL"
                          : "Your local or self-hosted Confluence URL (e.g., http://localhost:8090)"}
                      />
                      <Group grow>
                        <TextInput
                          label="Username or Email"
                          placeholder="user@company.com"
                          required
                          description="Your Confluence account username or email address"
                          {...form.getInputProps('confluence_config.username_or_email')}
                        />
                        <TextInput
                          label="API Token"
                          placeholder="Paste your Confluence API token"
                          type="password"
                          required
                          description="Your API token will be encrypted when saved"
                          {...form.getInputProps('confluence_config.api_token')}
                        />
                      </Group>
                      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light" title="API Token">
                        <Text size="sm">
                          Get your API token from {' '}
                          <Anchor href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank">
                            Atlassian API tokens
                          </Anchor>
                        </Text>
                      </Alert>

                      {/* Test Credentials Button */}
                      <Button
                        onClick={handleTestConfluenceCredentials}
                        loading={isTestingConfluenceCredentials}
                        variant="light"
                        color="cyan"
                        leftSection={<IconClipboardCheck size={16} />}
                        fullWidth
                      >
                        Test Credentials
                      </Button>

                      {/* Test Result Alert */}
                      {confluenceTestResult && (
                        <Alert
                          icon={confluenceTestResult.success ? <IconClipboardCheck size={16} /> : <IconX size={16} />}
                          color={confluenceTestResult.success ? 'green' : 'red'}
                          variant="light"
                          title={confluenceTestResult.success ? 'Credentials Valid' : 'Credentials Invalid'}
                        >
                          <Stack gap="xs">
                            <Text size="sm">{confluenceTestResult.message}</Text>
                            {confluenceTestResult.success && confluenceTestResult.spaces && confluenceTestResult.spaces.length > 0 && (
                              <Stack gap="xs">
                                <Text size="sm" fw={500}>Available Spaces:</Text>
                                <Stack gap="xs" style={{ paddingLeft: '12px' }}>
                                  {confluenceTestResult.spaces.map((space: any, idx: number) => (
                                    <Group key={idx} gap="xs">
                                      <Text size="sm" c="dimmed" style={{ fontFamily: 'monospace' }}>
                                        [{space.key}]
                                      </Text>
                                      <Text size="sm">{space.name}</Text>
                                    </Group>
                                  ))}
                                </Stack>
                              </Stack>
                            )}
                          </Stack>
                        </Alert>
                      )}
                    </Stack>

                    {/* Confluence Scraping Mode */}
                    <Select
                      label="Scraping Mode"
                      placeholder="Select scraping mode"
                      required
                      data={[
                        { value: 'space_pages', label: 'Space Pages', description: 'Extract all pages from specific spaces' },
                        { value: 'specific_pages', label: 'Specific Pages', description: 'Extract individual pages by ID' },
                        { value: 'pages_with_label', label: 'Pages with Labels', description: 'Extract pages matching labels' },
                        { value: 'recently_modified', label: 'Recently Modified', description: 'Extract recently changed pages' },
                      ].map(mode => ({
                        value: mode.value,
                        label: mode.label,
                        description: mode.description
                      }))}
                      description={
                        [
                          { value: 'space_pages', label: 'Space Pages', description: 'Extract all pages from specific spaces' },
                          { value: 'specific_pages', label: 'Specific Pages', description: 'Extract individual pages by ID' },
                          { value: 'pages_with_label', label: 'Pages with Labels', description: 'Extract pages matching labels' },
                          { value: 'recently_modified', label: 'Recently Modified', description: 'Extract recently changed pages' },
                        ].find(m => m.value === form.values.scraping_mode)?.description || 'Select a mode'
                      }
                      {...form.getInputProps('scraping_mode')}
                    />

                    {/* Mode-specific fields */}
                    {form.values.scraping_mode === 'space_pages' && (
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>Confluence Spaces</Text>

                        {/* Show available spaces if loaded */}
                        {availableSpaces.length > 0 && (
                          <Stack gap="xs" style={{
                            border: '1px solid #e9ecef',
                            borderRadius: '8px',
                            padding: '12px',
                            backgroundColor: '#f8f9fa'
                          }}>
                            <Text size="xs" fw={500}>Available Spaces - Click to Add:</Text>
                            <Stack gap="xs">
                              {availableSpaces.map((space, idx) => (
                                <Group
                                  key={idx}
                                  style={{
                                    padding: '8px 12px',
                                    borderRadius: '6px',
                                    backgroundColor: form.values.confluence_config.space_keys.includes(space.key)
                                      ? '#c5f015'
                                      : '#ffffff',
                                    border: '1px solid #dee2e6',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                  }}
                                  onClick={() => {
                                    const newKeys = form.values.confluence_config.space_keys.includes(space.key)
                                      ? form.values.confluence_config.space_keys.filter(k => k !== space.key)
                                      : [...form.values.confluence_config.space_keys, space.key];
                                    form.setFieldValue('confluence_config', {
                                      ...form.values.confluence_config,
                                      space_keys: newKeys
                                    });
                                  }}
                                >
                                  <Badge color={form.values.confluence_config.space_keys.includes(space.key) ? 'green' : 'gray'}>
                                    {space.key}
                                  </Badge>
                                  <Text size="sm" style={{ flex: 1 }}>{space.name}</Text>
                                  {form.values.confluence_config.space_keys.includes(space.key) && (
                                    <IconClipboardCheck size={16} color="green" />
                                  )}
                                </Group>
                              ))}
                            </Stack>
                          </Stack>
                        )}

                        {/* Manual entry section */}
                        <Text size="xs" c="dimmed">Or manually enter space keys:</Text>
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

                    {form.values.scraping_mode === 'specific_pages' && (
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

                    {form.values.scraping_mode === 'pages_with_label' && (
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
          )}

          {stepConfigs[activeStep]?.label === 'Domain Filtering' && (
            <Stack gap="md" mt="md">
              <Group grow align="flex-start">
                <div>
                  <Text size="sm" fw={500} mb="sm">Allowed Subdomains</Text>
                  <Stack gap="sm">
                    {form.values.allowed_subdomains.map((subdomain, index) => (
                      <Group key={index} gap="sm">
                        <TextInput
                          placeholder="subdomain.example.com"
                          value={subdomain}
                          onChange={(e) => updateSubdomain('allowed', index, e.currentTarget.value)}
                          style={{ flex: 1 }}
                        />
                        <ActionIcon
                          color="red"
                          variant="light"
                          onClick={() => removeSubdomain('allowed', index)}
                        >
                          <IconX size={16} />
                        </ActionIcon>
                      </Group>
                    ))}
                    <Button
                      variant="light"
                      leftSection={<IconPlus size={16} />}
                      onClick={() => addSubdomain('allowed')}
                      size="sm"
                    >
                      Add Allowed Subdomain
                    </Button>
                  </Stack>
                </div>

                <div>
                  <Text size="sm" fw={500} mb="sm">Blocked Subdomains</Text>
                  <Stack gap="sm">
                    {form.values.blocked_subdomains.map((subdomain, index) => (
                      <Group key={index} gap="sm">
                        <TextInput
                          placeholder="blocked.example.com"
                          value={subdomain}
                          onChange={(e) => updateSubdomain('blocked', index, e.currentTarget.value)}
                          style={{ flex: 1 }}
                        />
                        <ActionIcon
                          color="red"
                          variant="light"
                          onClick={() => removeSubdomain('blocked', index)}
                        >
                          <IconX size={16} />
                        </ActionIcon>
                      </Group>
                    ))}
                    <Button
                      variant="light"
                      leftSection={<IconPlus size={16} />}
                      onClick={() => addSubdomain('blocked')}
                      size="sm"
                    >
                      Add Blocked Subdomain
                    </Button>
                  </Stack>
                </div>
              </Group>

              <Divider label={<Text size="xs" c="dimmed">URL Patterns</Text>} labelPosition="center" />

              <Stack gap="sm">
                <Text size="sm" fw={500}>URL Patterns</Text>
                <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                  Define URL patterns to include or exclude from crawling. Use regex patterns for flexible matching.
                </Alert>

                {form.values.url_patterns.map((pattern, index) => (
                  <Group key={index} gap="sm" align="flex-end">
                    <TextInput
                      label={index === 0 ? "Pattern" : ""}
                      placeholder="https://example.com/.*"
                      value={pattern.pattern}
                      onChange={(e) => updateUrlPattern(index, 'pattern', e.currentTarget.value)}
                      style={{ flex: 2 }}
                    />
                    <Switch
                      label={index === 0 ? "Exclude" : ""}
                      description={index === 0 ? "Reverse pattern (exclude matching URLs)" : ""}
                      checked={pattern.reverse}
                      onChange={(e) => updateUrlPattern(index, 'reverse', e.currentTarget.checked)}
                      style={{ flex: 1 }}
                    />
                    <ActionIcon
                      color="red"
                      variant="light"
                      onClick={() => removeUrlPattern(index)}
                    >
                      <IconX size={16} />
                    </ActionIcon>
                  </Group>
                ))}

                <Button
                  variant="light"
                  leftSection={<IconPlus size={16} />}
                  onClick={addUrlPattern}
                  size="sm"
                >
                  Add URL Pattern
                </Button>
              </Stack>
            </Stack>
          )}

          {stepConfigs[activeStep]?.label === 'Content Filter' && (
            <Stack gap="md" mt="md">
              <Title order={3}>Content Filter</Title>
              <Text c="dimmed">
                Configure content extraction and filtering options.
              </Text>

              {/* Content Filter Step Container with Relative Positioning */}
              <div style={{ position: 'relative' }}>
                {/* Target Elements Section - Creative Layout */}
                <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                  <Stack gap="md">
                    {/* Header with Icon */}
                    <Group gap="xs" mb="sm">
                      <IconCode size={20} color="var(--mantine-color-blue-6)" />
                      <Text size="lg" fw={600} c="blue">Target Elements</Text>
                      <Badge size="sm" color="blue" variant="light">
                        {form.values.target_elements.length} selectors
                      </Badge>
                    </Group>

                    {/* Main Content - Two Column Layout */}
                    <Group align="flex-start" gap="lg">
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


                      </Stack>
                    </Group>

                  </Stack>
                </Card>

                {/* Floating Test Section - Within Content Filter Step */}
                {(form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) && (
                  <div style={{
                    position: 'absolute',
                    top: '20px',
                    right: '0px',
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
                              <Text size="lg" fw={600} c="cyan">Test Selectors</Text>
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

              </div>
            </Stack>
          )}

          {stepConfigs[activeStep]?.label === 'Generation' && (
            <Stack gap="md" mt="md">
              <Title order={3}>Generation</Title>
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
                              searchable
                              leftSection={<IconFilter size={16} />}
                            />

                            {form.values.llm_content_filter_id && contentFilters && (
                              (() => {
                                const selectedFilter = contentFilters.find((f: any) => f.id === form.values.llm_content_filter_id);
                                return selectedFilter ? (
                                  <Alert icon={<IconInfoCircle />} color="blue" title="Filter Details">
                                    <Stack gap="xs">
                                      <Text size="sm"><strong>Name:</strong> {selectedFilter.name}</Text>
                                      {selectedFilter.description && (
                                        <Text size="sm"><strong>Description:</strong> {selectedFilter.description}</Text>
                                      )}
                                      <Text size="sm"><strong>Model:</strong> {selectedFilter.llm_model_name}</Text>
                                      <Button
                                        variant="light"
                                        size="xs"
                                        leftSection={<IconEye size={14} />}
                                        onClick={() => {
                                          // Open modal to view instructions
                                          modals.open({
                                            title: (
                                              <Group gap="sm">
                                                <IconFilter size={20} color="var(--mantine-color-blue-6)" />
                                                <Text fw={600} size="lg" c="blue">LLM Content Filter Instructions</Text>
                                              </Group>
                                            ),
                                            children: (
                                              <Stack gap="md">
                                                <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                                                  <Stack gap="xs">
                                                    <Text size="sm" fw={500} c="blue">Filter: {selectedFilter.name}</Text>
                                                    <Text size="xs" c="dimmed">Model: {selectedFilter.llm_model_name}</Text>
                                                  </Stack>
                                                </Card>
                                                <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                                                  <Stack gap="sm">
                                                    <Text size="sm" fw={500}>Instructions:</Text>
                                                    <Text
                                                      size="sm"
                                                      style={{
                                                        fontFamily: 'monospace',
                                                        whiteSpace: 'pre-wrap',
                                                        lineHeight: 1.6
                                                      }}
                                                    >
                                                      {selectedFilter.instruction || 'No instructions provided'}
                                                    </Text>
                                                  </Stack>
                                                </Card>
                                              </Stack>
                                            ),
                                            size: 'lg',
                                            radius: 'md',
                                            shadow: 'xl',
                                            styles: {
                                              header: {
                                                backgroundColor: 'var(--mantine-color-blue-0)',
                                                borderBottom: '2px solid var(--mantine-color-blue-3)',
                                                padding: '20px 24px',
                                              },
                                              content: {
                                                backgroundColor: 'white',
                                                padding: '24px',
                                              },
                                              body: {
                                                padding: 0,
                                              }
                                            }
                                          });
                                        }}
                                      >
                                        View Instructions
                                      </Button>
                                    </Stack>
                                  </Alert>
                                ) : null;
                              })()
                            )}

                            <Divider />

                            <Alert icon={<IconInfoCircle />} color="gray">
                              <Text size="sm">
                                <strong>What are Content Filters?</strong>
                              </Text>
                              <Text size="sm" mt="xs">
                                Content filters use AI to extract only relevant content from crawled pages,
                                removing navigation elements, ads, footers, and other noise. This improves
                                the quality of your knowledge base.
                              </Text>
                            </Alert>

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
                {(form.values.url || (form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0)) && (
                  <div style={{
                    position: 'absolute',
                    top: '20px',
                    right: '0px',
                    zIndex: 100,
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
                              <Text size="lg" fw={600} c="cyan">Preview Content</Text>
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

              </div>
            </Stack>
          )}

          {stepConfigs[activeStep]?.label === 'Review' && (
            <Stack gap="md" mt="md">
              <Title order={3}>Review Configuration</Title>
              <Text c="dimmed">Review all your configuration settings before updating.</Text>

              {/* Basic Information Section */}
              <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                <Stack gap="md">
                  <Group gap="xs" align="center">
                    <IconSettings size={18} color="var(--mantine-color-blue-6)" />
                    <Text size="lg" fw={600} c="blue">Basic Information</Text>
                  </Group>

                  <Group gap="sm">
                    <Text fw={600} size="lg">{form.values.name}</Text>
                    <Badge color="blue" variant="light">
                      {form.values.content_source_type === 'local_files'
                        ? (form.values.scraping_mode === 'html_files' ? 'HTML Files' :
                          form.values.scraping_mode === 'markdown_files' ? 'Markdown Files' :
                            form.values.scraping_mode === 'pdf_files' ? 'PDF Files' :
                              form.values.scraping_mode === 'docx_files' ? 'DOCX Files' :
                                form.values.scraping_mode === 'txt_files' ? 'TXT Files' : 'Local Files')
                        : (form.values.scraping_mode === 'single_page' ? 'Single Page' :
                          form.values.scraping_mode === 'multiple_pages' ? 'Multiple Pages' :
                            'Website Crawler')}
                    </Badge>
                  </Group>

                  {form.values.description && (
                    <Text c="dimmed">{form.values.description}</Text>
                  )}

                  {/* Web Scraping specific info */}
                  {form.values.content_source_type === 'web_scraping' && (
                    <>
                      <Group gap="md">
                        <Group gap="xs">
                          <Text size="sm" fw={500}>URL:</Text>
                          <Text size="sm">{form.values.url}</Text>
                        </Group>
                      </Group>

                      {form.values.scraping_mode === 'multiple_pages' && form.values.url_source.urls.length > 0 && (
                        <Group gap="xs">
                          <Text size="sm" fw={500}>URLs from file:</Text>
                          <Text size="sm">{form.values.url_source.urls.length} URLs</Text>
                          {form.values.url_source.file_name && (
                            <Badge size="sm" color="blue" variant="light">{form.values.url_source.file_name}</Badge>
                          )}
                        </Group>
                      )}
                    </>
                  )}

                  {/* Local Files specific info */}
                  {form.values.content_source_type === 'local_files' && (
                    <Stack gap="md">
                      <Divider label="Files Summary" />

                      {/* Existing Files */}
                      {form.values.local_files && form.values.local_files.length > 0 && (
                        <Stack gap="xs">
                          <Group gap="xs">
                            <IconFileText size={16} color="var(--mantine-color-blue-6)" />
                            <Text size="sm" fw={600} c="blue">Current Files</Text>
                          </Group>
                          <Group gap="md">
                            <Group gap="xs">
                              <Text size="sm" fw={500}>Count:</Text>
                              <Badge size="sm" color="blue" variant="light">
                                {form.values.local_files.length} file{form.values.local_files.length !== 1 ? 's' : ''}
                              </Badge>
                            </Group>
                            <Group gap="xs">
                              <Text size="sm" fw={500}>Total Size:</Text>
                              <Badge size="sm" color="blue" variant="light">
                                {(form.values.local_files.reduce((sum: number, file: any) => sum + (file.file_size || 0), 0) / 1024 / 1024).toFixed(2)} MB
                              </Badge>
                            </Group>
                          </Group>
                        </Stack>
                      )}

                      {/* New Files to Upload */}
                      {newUploadedFiles.length > 0 && (
                        <Stack gap="xs">
                          <Group gap="xs">
                            <IconUpload size={16} color="var(--mantine-color-green-6)" />
                            <Text size="sm" fw={600} c="green">New Files to Upload</Text>
                          </Group>
                          <Group gap="md">
                            <Group gap="xs">
                              <Text size="sm" fw={500}>Count:</Text>
                              <Badge size="sm" color="green" variant="light">
                                {newUploadedFiles.length} file{newUploadedFiles.length !== 1 ? 's' : ''}
                              </Badge>
                            </Group>
                            <Group gap="xs">
                              <Text size="sm" fw={500}>Total Size:</Text>
                              <Badge size="sm" color="green" variant="light">
                                {(newUploadedFiles.reduce((sum, file) => sum + file.size, 0) / 1024 / 1024).toFixed(2)} MB
                              </Badge>
                            </Group>
                          </Group>
                        </Stack>
                      )}

                      {/* Combined Summary */}
                      <Stack gap="xs">
                        <Divider />
                        <Group gap="xs">
                          <Text size="sm" fw={600}>After Update:</Text>
                        </Group>
                        <Group gap="md">
                          <Group gap="xs">
                            <Text size="sm" fw={500}>Total Files:</Text>
                            <Badge size="sm" color="purple" variant="light">
                              {((form.values.local_files?.length || 0) + newUploadedFiles.length)} files
                            </Badge>
                          </Group>
                          <Group gap="xs">
                            <Text size="sm" fw={500}>Total Size:</Text>
                            <Badge size="sm" color="purple" variant="light">
                              {(
                                ((form.values.local_files?.reduce((sum: number, file: any) => sum + (file.file_size || 0), 0) || 0) / 1024 / 1024) +
                                (newUploadedFiles.reduce((sum, file) => sum + file.size, 0) / 1024 / 1024)
                              ).toFixed(2)} MB
                            </Badge>
                          </Group>
                        </Group>
                      </Stack>

                      {/* File List Preview */}
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>Files:</Text>
                        <Stack gap="xs" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                          {form.values.local_files?.map((file: any, index: number) => (
                            <Group key={file.file_id || index} gap="xs">
                              <IconFileText size={14} />
                              <Text size="xs" style={{ fontFamily: 'monospace', flex: 1 }}>
                                {file.original_filename}
                              </Text>
                              <Badge size="xs" variant="light" color="blue">
                                {(file.file_size / 1024).toFixed(2)} KB
                              </Badge>
                            </Group>
                          ))}
                          {newUploadedFiles.map((file: File, index: number) => (
                            <Group key={`new-${index}`} gap="xs">
                              <IconUpload size={14} color="var(--mantine-color-green-6)" />
                              <Text size="xs" style={{ fontFamily: 'monospace', flex: 1 }}>
                                {file.name}
                              </Text>
                              <Badge size="xs" variant="light" color="green">
                                {(file.size / 1024).toFixed(2)} KB
                              </Badge>
                              <Badge size="xs" variant="filled" color="green">
                                NEW
                              </Badge>
                            </Group>
                          ))}
                        </Stack>
                      </Stack>
                    </Stack>
                  )}
                </Stack>
              </Card>

              {/* Domain & URL Filtering Section - Only for Web Scraping */}
              {form.values.content_source_type === 'web_scraping' && (
                <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                  <Stack gap="md">
                    <Group gap="xs" align="center">
                      <IconFilter size={18} color="var(--mantine-color-green-6)" />
                      <Text size="lg" fw={600} c="green">Domain & URL Filtering</Text>
                    </Group>

                    <Group gap="md">
                      <Group gap="xs">
                        <Text size="sm" fw={500}>Crawl Depth:</Text>
                        <Text size="sm">{form.values.crawl_depth}</Text>
                      </Group>
                    </Group>

                    {form.values.allowed_subdomains.length > 0 && (
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>Allowed Subdomains:</Text>
                        <Group gap="xs" wrap="wrap">
                          {form.values.allowed_subdomains.map((subdomain, index) => (
                            <Badge key={index} size="sm" color="green" variant="light">{subdomain}</Badge>
                          ))}
                        </Group>
                      </Stack>
                    )}

                    {form.values.blocked_subdomains.length > 0 && (
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>Blocked Subdomains:</Text>
                        <Group gap="xs" wrap="wrap">
                          {form.values.blocked_subdomains.map((subdomain, index) => (
                            <Badge key={index} size="sm" color="red" variant="light">{subdomain}</Badge>
                          ))}
                        </Group>
                      </Stack>
                    )}

                    {form.values.url_patterns.length > 0 && (
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>URL Patterns:</Text>
                        {form.values.url_patterns.map((pattern, index) => (
                          <Group key={index} gap="xs">
                            <Text size="sm" ff="monospace">{pattern.pattern}</Text>
                            <Badge size="sm" color={pattern.reverse ? "red" : "green"} variant="light">
                              {pattern.reverse ? "Exclude" : "Include"}
                            </Badge>
                          </Group>
                        ))}
                      </Stack>
                    )}

                    {form.values.allowed_subdomains.length === 0 &&
                      form.values.blocked_subdomains.length === 0 &&
                      form.values.url_patterns.length === 0 && (
                        <Text size="sm" c="dimmed">No domain or URL filtering configured</Text>
                      )}
                  </Stack>
                </Card>
              )}

              {/* Content Filter Section - Only for Web Scraping or HTML Files */}
              {(form.values.content_source_type === 'web_scraping' || form.values.scraping_mode === 'html_files') && (
                <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                  <Stack gap="md">
                    <Group gap="xs" align="center">
                      <IconCode size={18} color="var(--mantine-color-cyan-6)" />
                      <Text size="lg" fw={600} c="cyan">Content Filter</Text>
                    </Group>

                    <Stack gap="xs">
                      <Text size="sm" fw={500}>Target Elements ({form.values.target_elements.length} total):</Text>
                      <Group gap="xs" wrap="wrap">
                        {form.values.target_elements.map((selector, index) => (
                          <Badge key={index} size="sm" color="cyan" variant="light" style={{ fontFamily: 'monospace' }}>
                            {selector}
                          </Badge>
                        ))}
                      </Group>
                    </Stack>

                  </Stack>
                </Card>
              )}

              {/* Generation Section - Only show for web scraping or file types that need generation (not markdown) */}
              {(form.values.content_source_type === 'web_scraping' ||
                form.values.scraping_mode === 'html_files' ||
                form.values.scraping_mode === 'pdf_files' ||
                form.values.scraping_mode === 'docx_files' ||
                form.values.scraping_mode === 'txt_files') && (
                  <Card withBorder p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                    <Stack gap="md">
                      <Group gap="xs" align="center">
                        <IconWand
                          size={24}
                          color="#8b5cf6"
                          style={{
                            filter: 'drop-shadow(0 0 8px rgba(139, 92, 246, 0.4))',
                            transform: 'rotate(-15deg)'
                          }}
                        />
                        <Text size="lg" fw={600} c="purple">Generation</Text>
                      </Group>

                      <Group gap="md">
                        <Group gap="xs">
                          <Text size="sm" fw={500}>Output Format:</Text>
                          <Badge size="sm" color="purple" variant="light">
                            {form.values.output_format === 'html' ? 'Raw HTML' : 'Markdown'}
                          </Badge>
                        </Group>
                        <Group gap="xs">
                          <Text size="sm" fw={500}>Current Value:</Text>
                          <Text size="sm" ff="monospace" c="dimmed">{form.values.output_format}</Text>
                        </Group>
                      </Group>

                      {form.values.output_format === 'markdown' && (
                        <Group gap="md">
                          <Group gap="xs">
                            <Text size="sm" fw={500}>Generation Method:</Text>
                            <Badge size="sm" color={form.values.markdown_generation === 'llm' ? 'orange' : 'blue'} variant="light">
                              {form.values.markdown_generation === 'llm' ? 'LLM-Powered' : 'Standard'}
                            </Badge>
                          </Group>

                          {form.values.markdown_generation === 'standard' && (
                            <Group gap="xs">
                              <Text size="sm" fw={500}>Threshold:</Text>
                              <Text size="sm">{form.values.content_filter_threshold}</Text>
                            </Group>
                          )}
                        </Group>
                      )}

                      {/* LLM Content Filter Section */}
                      {form.values.output_format === 'markdown' && form.values.markdown_generation === 'llm' && (
                        <Stack gap="md">
                          <Divider label="LLM Content Filter" />

                          {form.values.llm_content_filter_id && (
                            form.values.llm_content_filter_id === 'new' && form.values.new_llm_filter ? (
                              <Stack gap="xs">
                                <Text size="sm" fw={500}>New LLM Filter:</Text>
                                <Group gap="xs">
                                  <Text size="sm">{form.values.new_llm_filter.name}</Text>
                                  <Badge size="sm" color="blue" variant="light">New</Badge>
                                </Group>
                                {form.values.new_llm_filter.description && (
                                  <Text size="sm" c="dimmed">{form.values.new_llm_filter.description}</Text>
                                )}
                                <Group gap="md">
                                  <Group gap="xs">
                                    <Text size="sm" fw={500}>Model:</Text>
                                    <Text size="sm">{form.values.new_llm_filter.llm_model_name}</Text>
                                  </Group>
                                  <Group gap="xs">
                                    <Text size="sm" fw={500}>Temperature:</Text>
                                    <Text size="sm">{form.values.new_llm_filter.temperature}</Text>
                                  </Group>
                                  <Group gap="xs">
                                    <Text size="sm" fw={500}>Max Retries:</Text>
                                    <Text size="sm">{form.values.new_llm_filter.max_retries}</Text>
                                  </Group>
                                </Group>
                              </Stack>
                            ) : contentFilters ? (
                              (() => {
                                const selectedFilter = contentFilters.find((f: any) => f.id === form.values.llm_content_filter_id);
                                return selectedFilter ? (
                                  <Stack gap="xs">
                                    <Text size="sm" fw={500}>LLM Filter:</Text>
                                    <Group gap="xs">
                                      <Text size="sm">{selectedFilter.name}</Text>
                                      <Badge size="sm" color="green" variant="light">Existing</Badge>
                                    </Group>
                                    {selectedFilter.description && (
                                      <Text size="sm" c="dimmed">{selectedFilter.description}</Text>
                                    )}
                                    <Group gap="md">
                                      <Group gap="xs">
                                        <Text size="sm" fw={500}>Model:</Text>
                                        <Text size="sm">{selectedFilter.llm_model_name}</Text>
                                      </Group>
                                      <Group gap="xs">
                                        <Text size="sm" fw={500}>Temperature:</Text>
                                        <Text size="sm">{selectedFilter.temperature || 0}</Text>
                                      </Group>
                                      <Group gap="xs">
                                        <Text size="sm" fw={500}>Max Retries:</Text>
                                        <Text size="sm">{selectedFilter.max_retries}</Text>
                                      </Group>
                                    </Group>
                                  </Stack>
                                ) : (
                                  <Text size="sm" c="orange">Selected filter not found</Text>
                                );
                              })()
                            ) : null
                          )}

                          {!form.values.llm_content_filter_id && (
                            <Text size="sm" c="dimmed">No LLM content filter configured</Text>
                          )}
                        </Stack>
                      )}
                    </Stack>
                  </Card>
                )}
            </Stack>
          )}
        </ColorfulVerticalStepper>

        <Group justify="space-between" mt="xl">
          <div />

          <Group>
            <Button
              variant="default"
              onClick={prevStep}
              disabled={activeStep === 0}
            >
              Previous
            </Button>

            {activeStep < stepConfigs.length - 1 ? (
              <Button onClick={nextStep} disabled={!validateStep(activeStep)}>
                Next
              </Button>
            ) : (
              <Button
                onClick={() => handleSubmit(form.values)}
                loading={updateConfigMutation.isPending}
                disabled={!validateStep(activeStep)}
              >
                Update Configuration
              </Button>
            )}
          </Group>
        </Group>
      </form>

      {/* URLs Modal */}
      <Modal
        opened={urlsModalOpen}
        onClose={() => setUrlsModalOpen(false)}
        title={
          <Group gap="sm">
            <IconLink size={20} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="lg">URL List</Text>
            {config?.url_source_id && (
              <Text size="xs" c="dimmed" ff="monospace">({config.url_source_id})</Text>
            )}
          </Group>
        }
        centered
        size="lg"
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
        }}
      >
        <Stack gap="md">
          {urlSourceLoading ? (
            <Center py="xl">
              <Loader size="md" />
            </Center>
          ) : form.values.url_source.urls.length > 0 ? (
            <>
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  {form.values.url_source.file_name && `File: ${form.values.url_source.file_name}`}
                </Text>
                <Badge color="blue" variant="light">
                  {form.values.url_source.urls.length} URLs
                </Badge>
              </Group>

              <ScrollArea h={400}>
                <List spacing="xs" size="sm">
                  {form.values.url_source.urls.map((url, index) => (
                    <List.Item
                      key={index}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        backgroundColor: 'var(--mantine-color-gray-0)',
                        border: '1px solid var(--mantine-color-gray-2)',
                        marginBottom: '4px',
                      }}
                    >
                      <Group justify="space-between" wrap="nowrap">
                        <Anchor
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          size="sm"
                          style={{
                            flex: 1,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {url}
                        </Anchor>
                        <Group gap={4}>
                          <CopyButton value={url}>
                            {({ copied, copy }) => (
                              <Tooltip label={copied ? 'Copied' : 'Copy URL'}>
                                <ActionIcon
                                  color={copied ? 'teal' : 'gray'}
                                  variant="subtle"
                                  onClick={copy}
                                  size="sm"
                                >
                                  <IconCopy size={14} />
                                </ActionIcon>
                              </Tooltip>
                            )}
                          </CopyButton>
                          <Tooltip label="Open in new tab">
                            <ActionIcon
                              component="a"
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              variant="subtle"
                              color="gray"
                              size="sm"
                            >
                              <IconExternalLink size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Group>
                    </List.Item>
                  ))}
                </List>
              </ScrollArea>
            </>
          ) : (
            <Center py="xl">
              <Text c="dimmed">No URLs loaded</Text>
            </Center>
          )}
        </Stack>
      </Modal>

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
            <Text fw={600} size="lg">Create Content Filter</Text>
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
              <Button type="submit">
                Create Filter
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

    </Page>
  );
}