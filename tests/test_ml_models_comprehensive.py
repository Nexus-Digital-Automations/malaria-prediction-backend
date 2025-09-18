"""
Comprehensive unit tests for machine learning models.

Tests LSTM, Transformer, and Ensemble models for malaria prediction
including model architecture, training, inference, and error handling.
"""


import pytest
import torch

from src.malaria_predictor.ml.models.ensemble_model import (
    EnsembleConfig,
    EnsembleModel,
    MalariaEnsembleModel,
)
from src.malaria_predictor.ml.models.lstm_model import (
    LSTMConfig,
    LSTMModel,
    MalariaLSTM,
)
from src.malaria_predictor.ml.models.transformer_model import (
    MalariaTransformer,
    TransformerConfig,
    TransformerModel,
)


class TestLSTMConfig:
    """Test LSTM configuration model."""

    def test_default_config(self):
        """Test default LSTM configuration."""
        config = LSTMConfig()
        assert config.input_dim == 10
        assert config.hidden_dim == 64
        assert config.num_layers == 2
        assert config.dropout == 0.2
        assert config.bidirectional is False
        assert config.output_dim == 1

    def test_custom_config(self):
        """Test custom LSTM configuration."""
        config = LSTMConfig(
            input_dim=15,
            hidden_dim=128,
            num_layers=3,
            dropout=0.3,
            bidirectional=True,
            output_dim=4
        )
        assert config.input_dim == 15
        assert config.hidden_dim == 128
        assert config.num_layers == 3
        assert config.dropout == 0.3
        assert config.bidirectional is True
        assert config.output_dim == 4


class TestLSTMModel:
    """Test LSTM model architecture."""

    @pytest.fixture
    def lstm_config(self):
        """Test LSTM configuration."""
        return LSTMConfig(
            input_dim=8,
            hidden_dim=32,
            num_layers=2,
            dropout=0.1,
            bidirectional=False,
            output_dim=1
        )

    @pytest.fixture
    def lstm_model(self, lstm_config):
        """Test LSTM model instance."""
        return LSTMModel(lstm_config)

    def test_model_creation(self, lstm_model, lstm_config):
        """Test LSTM model creation."""
        assert isinstance(lstm_model, torch.nn.Module)
        assert lstm_model.config == lstm_config
        assert hasattr(lstm_model, 'lstm')
        assert hasattr(lstm_model, 'dropout')
        assert hasattr(lstm_model, 'linear')

    def test_forward_pass(self, lstm_model):
        """Test LSTM forward pass."""
        batch_size = 4
        sequence_length = 10
        input_dim = 8

        # Create test input
        x = torch.randn(batch_size, sequence_length, input_dim)

        # Forward pass
        output = lstm_model(x)

        # Check output shape
        assert output.shape == (batch_size, 1)
        assert output.dtype == torch.float32
        assert not torch.isnan(output).any()

    def test_bidirectional_model(self):
        """Test bidirectional LSTM model."""
        config = LSTMConfig(
            input_dim=8,
            hidden_dim=32,
            num_layers=2,
            bidirectional=True,
            output_dim=1
        )
        model = LSTMModel(config)

        batch_size = 4
        sequence_length = 10
        x = torch.randn(batch_size, sequence_length, 8)

        output = model(x)
        assert output.shape == (batch_size, 1)

    def test_model_parameters(self, lstm_model):
        """Test model parameter count."""
        total_params = sum(p.numel() for p in lstm_model.parameters())
        trainable_params = sum(p.numel() for p in lstm_model.parameters() if p.requires_grad)

        assert total_params > 0
        assert trainable_params > 0
        assert trainable_params == total_params  # All parameters should be trainable

    def test_model_training_mode(self, lstm_model):
        """Test model training/evaluation mode switching."""
        # Model should start in training mode
        assert lstm_model.training

        # Switch to evaluation mode
        lstm_model.eval()
        assert not lstm_model.training

        # Switch back to training mode
        lstm_model.train()
        assert lstm_model.training


class TestMalariaLSTM:
    """Test Malaria-specific LSTM implementation."""

    @pytest.fixture
    def malaria_lstm_config(self):
        """Malaria LSTM configuration."""
        return LSTMConfig(
            input_dim=10,  # Environmental features
            hidden_dim=64,
            num_layers=2,
            dropout=0.2,
            bidirectional=False,
            output_dim=1  # Risk score
        )

    @pytest.fixture
    def malaria_lstm(self, malaria_lstm_config):
        """Malaria LSTM model instance."""
        return MalariaLSTM(malaria_lstm_config)

    def test_malaria_lstm_creation(self, malaria_lstm, malaria_lstm_config):
        """Test Malaria LSTM creation."""
        assert isinstance(malaria_lstm, MalariaLSTM)
        assert malaria_lstm.config == malaria_lstm_config
        assert hasattr(malaria_lstm, 'model_info')

    def test_predict_risk(self, malaria_lstm):
        """Test malaria risk prediction."""
        # Environmental data for 30 days (sequence)
        environmental_data = torch.randn(1, 30, 10)  # batch=1, seq=30, features=10

        with torch.no_grad():
            risk_score = malaria_lstm.predict_risk(environmental_data)

        assert isinstance(risk_score, torch.Tensor)
        assert risk_score.shape == (1, 1)
        assert 0.0 <= risk_score.item() <= 1.0  # Should be a probability

    def test_feature_extraction(self, malaria_lstm):
        """Test feature extraction from environmental data."""
        environmental_data = torch.randn(2, 20, 10)

        with torch.no_grad():
            features = malaria_lstm.extract_features(environmental_data)

        assert isinstance(features, torch.Tensor)
        assert features.shape[0] == 2  # Batch size preserved
        assert features.ndim == 2  # Should be flattened features

    def test_model_info(self, malaria_lstm):
        """Test model information."""
        info = malaria_lstm.get_model_info()

        assert 'name' in info
        assert 'version' in info
        assert 'description' in info
        assert 'parameters' in info
        assert info['name'] == "Malaria LSTM Predictor"
        assert isinstance(info['parameters'], int)
        assert info['parameters'] > 0


class TestTransformerConfig:
    """Test Transformer configuration model."""

    def test_default_transformer_config(self):
        """Test default Transformer configuration."""
        config = TransformerConfig()
        assert config.input_dim == 10
        assert config.model_dim == 64
        assert config.num_heads == 8
        assert config.num_layers == 6
        assert config.feedforward_dim == 256
        assert config.dropout == 0.1
        assert config.max_sequence_length == 365
        assert config.output_dim == 1

    def test_custom_transformer_config(self):
        """Test custom Transformer configuration."""
        config = TransformerConfig(
            input_dim=15,
            model_dim=128,
            num_heads=16,
            num_layers=8,
            feedforward_dim=512,
            dropout=0.2,
            max_sequence_length=730,
            output_dim=4
        )
        assert config.input_dim == 15
        assert config.model_dim == 128
        assert config.num_heads == 16
        assert config.num_layers == 8
        assert config.feedforward_dim == 512
        assert config.dropout == 0.2
        assert config.max_sequence_length == 730
        assert config.output_dim == 4


class TestTransformerModel:
    """Test Transformer model architecture."""

    @pytest.fixture
    def transformer_config(self):
        """Test Transformer configuration."""
        return TransformerConfig(
            input_dim=8,
            model_dim=32,
            num_heads=4,
            num_layers=2,
            feedforward_dim=64,
            dropout=0.1,
            max_sequence_length=100,
            output_dim=1
        )

    @pytest.fixture
    def transformer_model(self, transformer_config):
        """Test Transformer model instance."""
        return TransformerModel(transformer_config)

    def test_transformer_creation(self, transformer_model, transformer_config):
        """Test Transformer model creation."""
        assert isinstance(transformer_model, torch.nn.Module)
        assert transformer_model.config == transformer_config
        assert hasattr(transformer_model, 'input_projection')
        assert hasattr(transformer_model, 'positional_encoding')
        assert hasattr(transformer_model, 'transformer')
        assert hasattr(transformer_model, 'output_projection')

    def test_transformer_forward_pass(self, transformer_model):
        """Test Transformer forward pass."""
        batch_size = 2
        sequence_length = 20
        input_dim = 8

        # Create test input
        x = torch.randn(batch_size, sequence_length, input_dim)

        # Forward pass
        output = transformer_model(x)

        # Check output shape
        assert output.shape == (batch_size, 1)
        assert output.dtype == torch.float32
        assert not torch.isnan(output).any()

    def test_attention_mechanism(self, transformer_model):
        """Test attention mechanism works correctly."""
        batch_size = 1
        sequence_length = 10
        input_dim = 8

        x = torch.randn(batch_size, sequence_length, input_dim)

        # Get attention weights
        with torch.no_grad():
            # Hook to capture attention weights
            attention_weights = []

            def attention_hook(module, input, output):
                attention_weights.append(output[1])  # Attention weights

            # Register hook
            for layer in transformer_model.transformer.layers:
                layer.self_attn.register_forward_hook(attention_hook)

            _ = transformer_model(x)

        # Check attention weights shape
        assert len(attention_weights) > 0
        for attn in attention_weights:
            assert attn.shape[0] == batch_size
            assert attn.shape[-1] == sequence_length  # Attention over sequence


class TestMalariaTransformer:
    """Test Malaria-specific Transformer implementation."""

    @pytest.fixture
    def malaria_transformer_config(self):
        """Malaria Transformer configuration."""
        return TransformerConfig(
            input_dim=12,  # Extended environmental features
            model_dim=64,
            num_heads=8,
            num_layers=4,
            feedforward_dim=256,
            dropout=0.1,
            max_sequence_length=365,  # 1 year of daily data
            output_dim=1
        )

    @pytest.fixture
    def malaria_transformer(self, malaria_transformer_config):
        """Malaria Transformer model instance."""
        return MalariaTransformer(malaria_transformer_config)

    def test_malaria_transformer_creation(self, malaria_transformer):
        """Test Malaria Transformer creation."""
        assert isinstance(malaria_transformer, MalariaTransformer)
        assert hasattr(malaria_transformer, 'model_info')

    def test_temporal_attention(self, malaria_transformer):
        """Test temporal attention for malaria prediction."""
        # Simulate 60 days of environmental data
        environmental_data = torch.randn(1, 60, 12)

        with torch.no_grad():
            risk_prediction = malaria_transformer.predict_temporal_risk(environmental_data)

        assert isinstance(risk_prediction, torch.Tensor)
        assert risk_prediction.shape == (1, 1)
        assert 0.0 <= risk_prediction.item() <= 1.0

    def test_feature_importance(self, malaria_transformer):
        """Test feature importance extraction."""
        environmental_data = torch.randn(1, 30, 12)

        importance_scores = malaria_transformer.get_feature_importance(environmental_data)

        assert isinstance(importance_scores, torch.Tensor)
        assert importance_scores.shape == (12,)  # One score per feature
        assert torch.all(importance_scores >= 0)  # Importance should be non-negative
        assert torch.isclose(importance_scores.sum(), torch.tensor(1.0), atol=1e-5)  # Should sum to 1


class TestEnsembleModel:
    """Test Ensemble model combining LSTM and Transformer."""

    @pytest.fixture
    def ensemble_config(self):
        """Ensemble configuration."""
        return EnsembleConfig(
            lstm_config=LSTMConfig(
                input_dim=10,
                hidden_dim=32,
                num_layers=2,
                dropout=0.1
            ),
            transformer_config=TransformerConfig(
                input_dim=10,
                model_dim=32,
                num_heads=4,
                num_layers=2,
                feedforward_dim=64,
                dropout=0.1,
                max_sequence_length=100
            ),
            ensemble_weights=[0.6, 0.4],  # LSTM weight, Transformer weight
            voting_strategy="weighted"
        )

    @pytest.fixture
    def ensemble_model(self, ensemble_config):
        """Ensemble model instance."""
        return EnsembleModel(ensemble_config)

    def test_ensemble_creation(self, ensemble_model, ensemble_config):
        """Test Ensemble model creation."""
        assert isinstance(ensemble_model, EnsembleModel)
        assert ensemble_model.config == ensemble_config
        assert hasattr(ensemble_model, 'lstm_model')
        assert hasattr(ensemble_model, 'transformer_model')
        assert hasattr(ensemble_model, 'ensemble_weights')

    def test_ensemble_prediction(self, ensemble_model):
        """Test ensemble prediction."""
        batch_size = 2
        sequence_length = 30
        input_dim = 10

        environmental_data = torch.randn(batch_size, sequence_length, input_dim)

        with torch.no_grad():
            ensemble_output = ensemble_model(environmental_data)

        assert ensemble_output.shape == (batch_size, 1)
        assert torch.all(ensemble_output >= 0.0)
        assert torch.all(ensemble_output <= 1.0)

    def test_individual_model_predictions(self, ensemble_model):
        """Test individual model predictions."""
        batch_size = 1
        sequence_length = 20
        input_dim = 10

        environmental_data = torch.randn(batch_size, sequence_length, input_dim)

        with torch.no_grad():
            predictions = ensemble_model.get_individual_predictions(environmental_data)

        assert 'lstm' in predictions
        assert 'transformer' in predictions
        assert 'ensemble' in predictions

        assert predictions['lstm'].shape == (batch_size, 1)
        assert predictions['transformer'].shape == (batch_size, 1)
        assert predictions['ensemble'].shape == (batch_size, 1)

    def test_ensemble_weights_validation(self):
        """Test ensemble weights validation."""
        config = EnsembleConfig(
            lstm_config=LSTMConfig(),
            transformer_config=TransformerConfig(),
            ensemble_weights=[0.7, 0.3],
            voting_strategy="weighted"
        )

        model = EnsembleModel(config)
        assert abs(sum(model.ensemble_weights) - 1.0) < 1e-5  # Should sum to 1

    def test_model_uncertainty(self, ensemble_model):
        """Test uncertainty estimation."""
        batch_size = 1
        sequence_length = 15
        input_dim = 10

        environmental_data = torch.randn(batch_size, sequence_length, input_dim)

        with torch.no_grad():
            uncertainty = ensemble_model.estimate_uncertainty(environmental_data)

        assert isinstance(uncertainty, torch.Tensor)
        assert uncertainty.shape == (batch_size, 1)
        assert torch.all(uncertainty >= 0.0)  # Uncertainty should be non-negative


class TestMalariaEnsembleModel:
    """Test Malaria-specific Ensemble implementation."""

    @pytest.fixture
    def malaria_ensemble_config(self):
        """Malaria Ensemble configuration."""
        return EnsembleConfig(
            lstm_config=LSTMConfig(
                input_dim=15,  # Rich environmental features
                hidden_dim=64,
                num_layers=3,
                dropout=0.2,
                bidirectional=True
            ),
            transformer_config=TransformerConfig(
                input_dim=15,
                model_dim=128,
                num_heads=8,
                num_layers=6,
                feedforward_dim=512,
                dropout=0.1,
                max_sequence_length=365
            ),
            ensemble_weights=[0.5, 0.5],
            voting_strategy="weighted"
        )

    @pytest.fixture
    def malaria_ensemble(self, malaria_ensemble_config):
        """Malaria Ensemble model instance."""
        return MalariaEnsembleModel(malaria_ensemble_config)

    def test_malaria_ensemble_creation(self, malaria_ensemble):
        """Test Malaria Ensemble creation."""
        assert isinstance(malaria_ensemble, MalariaEnsembleModel)
        assert hasattr(malaria_ensemble, 'model_info')

    def test_outbreak_prediction(self, malaria_ensemble):
        """Test outbreak prediction with confidence intervals."""
        # 90 days of environmental data
        environmental_data = torch.randn(1, 90, 15)

        prediction_result = malaria_ensemble.predict_outbreak_risk(
            environmental_data,
            include_confidence=True
        )

        assert 'risk_score' in prediction_result
        assert 'confidence_interval' in prediction_result
        assert 'model_agreement' in prediction_result

        risk_score = prediction_result['risk_score']
        assert 0.0 <= risk_score <= 1.0

        ci = prediction_result['confidence_interval']
        assert ci['lower'] <= risk_score <= ci['upper']
        assert 0.0 <= ci['lower'] <= ci['upper'] <= 1.0

    def test_seasonal_analysis(self, malaria_ensemble):
        """Test seasonal malaria risk analysis."""
        # Full year of daily data
        environmental_data = torch.randn(1, 365, 15)

        seasonal_risks = malaria_ensemble.analyze_seasonal_patterns(environmental_data)

        assert 'monthly_risks' in seasonal_risks
        assert 'peak_months' in seasonal_risks
        assert 'seasonal_trend' in seasonal_risks

        monthly_risks = seasonal_risks['monthly_risks']
        assert len(monthly_risks) == 12  # 12 months
        assert all(0.0 <= risk <= 1.0 for risk in monthly_risks)

    def test_model_explainability(self, malaria_ensemble):
        """Test model explainability features."""
        environmental_data = torch.randn(1, 30, 15)

        explanation = malaria_ensemble.explain_prediction(environmental_data)

        assert 'feature_importance' in explanation
        assert 'temporal_importance' in explanation
        assert 'model_contributions' in explanation

        feature_importance = explanation['feature_importance']
        assert len(feature_importance) == 15  # Number of input features
        assert all(importance >= 0 for importance in feature_importance)


class TestModelIntegration:
    """Test model integration and compatibility."""

    def test_model_serialization(self):
        """Test model save/load functionality."""
        config = LSTMConfig(input_dim=8, hidden_dim=32, num_layers=2)
        model = LSTMModel(config)

        # Test state dict serialization
        state_dict = model.state_dict()
        assert isinstance(state_dict, dict)
        assert len(state_dict) > 0

        # Create new model and load state
        new_model = LSTMModel(config)
        new_model.load_state_dict(state_dict)

        # Test that models produce same output
        test_input = torch.randn(1, 10, 8)
        with torch.no_grad():
            output1 = model(test_input)
            output2 = new_model(test_input)

        assert torch.allclose(output1, output2, atol=1e-6)

    def test_model_device_compatibility(self):
        """Test model device (CPU/GPU) compatibility."""
        config = LSTMConfig(input_dim=5, hidden_dim=16, num_layers=1)
        model = LSTMModel(config)

        # Test CPU
        assert next(model.parameters()).device.type == 'cpu'

        test_input = torch.randn(1, 5, 5)
        output = model(test_input)
        assert output.device.type == 'cpu'

        # Test GPU if available
        if torch.cuda.is_available():
            model_gpu = model.cuda()
            test_input_gpu = test_input.cuda()
            output_gpu = model_gpu(test_input_gpu)
            assert output_gpu.device.type == 'cuda'

    def test_batch_size_flexibility(self):
        """Test models work with different batch sizes."""
        config = LSTMConfig(input_dim=6, hidden_dim=24, num_layers=2)
        model = LSTMModel(config)

        sequence_length = 15
        input_dim = 6

        # Test different batch sizes
        for batch_size in [1, 4, 16, 32]:
            test_input = torch.randn(batch_size, sequence_length, input_dim)
            with torch.no_grad():
                output = model(test_input)
            assert output.shape == (batch_size, 1)

    def test_sequence_length_flexibility(self):
        """Test models work with different sequence lengths."""
        config = TransformerConfig(
            input_dim=8,
            model_dim=32,
            num_heads=4,
            num_layers=2,
            max_sequence_length=200
        )
        model = TransformerModel(config)

        batch_size = 2
        input_dim = 8

        # Test different sequence lengths
        for seq_len in [10, 50, 100, 150]:
            test_input = torch.randn(batch_size, seq_len, input_dim)
            with torch.no_grad():
                output = model(test_input)
            assert output.shape == (batch_size, 1)


class TestErrorHandling:
    """Test error handling in ML models."""

    def test_invalid_config_validation(self):
        """Test validation of invalid configurations."""
        # Test invalid LSTM config
        with pytest.raises((ValueError, TypeError)):
            LSTMConfig(input_dim=-1)  # Negative input dimension

        with pytest.raises((ValueError, TypeError)):
            LSTMConfig(num_layers=0)  # Zero layers

        # Test invalid Transformer config
        with pytest.raises((ValueError, TypeError)):
            TransformerConfig(num_heads=0)  # Zero attention heads

        with pytest.raises((ValueError, TypeError)):
            TransformerConfig(model_dim=63, num_heads=8)  # model_dim not divisible by num_heads

    def test_input_shape_validation(self):
        """Test input shape validation."""
        config = LSTMConfig(input_dim=10, hidden_dim=32, num_layers=2)
        model = LSTMModel(config)

        # Test wrong input dimension
        with pytest.raises(RuntimeError):
            wrong_input = torch.randn(1, 20, 5)  # Wrong feature dimension
            model(wrong_input)

        # Test 2D input (missing sequence dimension)
        with pytest.raises((RuntimeError, IndexError)):
            wrong_input = torch.randn(1, 10)  # Missing sequence dimension
            model(wrong_input)

    def test_gradient_flow(self):
        """Test gradient flow in models."""
        config = LSTMConfig(input_dim=8, hidden_dim=32, num_layers=2)
        model = LSTMModel(config)

        # Create input that requires gradients
        test_input = torch.randn(2, 10, 8, requires_grad=True)

        # Forward pass
        output = model(test_input)
        loss = output.mean()

        # Backward pass
        loss.backward()

        # Check gradients exist
        assert test_input.grad is not None
        assert not torch.isnan(test_input.grad).any()

        # Check model parameter gradients
        for param in model.parameters():
            assert param.grad is not None
            assert not torch.isnan(param.grad).any()
