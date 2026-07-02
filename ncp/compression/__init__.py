"""NCP Compression - Dynamic, policy-based compression."""

from ncp.compression.abstraction import AbstractionCompressor
from ncp.compression.decoder import Decoder
from ncp.compression.dictionary import CompressionDictionary
from ncp.compression.encoder import Encoder
from ncp.compression.grammar import GraphGrammar
from ncp.compression.manager import CompressionManager
from ncp.compression.statistics import CompressionStatistics

__all__ = [
    "AbstractionCompressor",
    "GraphGrammar","CompressionManager", "Encoder", "Decoder", "CompressionDictionary", "CompressionStatistics"]
